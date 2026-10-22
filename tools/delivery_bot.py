#!/usr/bin/env python3
"""Business Fox backup delivery bot.

Runs in GitHub Actions (see .github/workflows/delivery-bot.yml). It never edits store pages,
so it can't get in the way of Business-Fox. Every run:

  1. Reads COMPLETED (fully captured) Square payments. Card, Apple Pay, Google Pay and Cash App Pay
     all count. Payments that are only approved, pending, failed or refunded are never fulfilled.
  2. Matches each paid line item to a store product (catalog.json + tools/delivery_bot.json).
  3. Waits a grace period so Business-Fox can deliver first.
  4. Checks the store Gmail "Sent" mail for a message to the buyer after the payment.
     Found -> marked "delivered by AI". Not found -> the bot delivers:
        printable product -> emails the PDF
        service / website -> emails the "send us your brief" next-step message
     and alerts the owner.
  5. Saves the encrypted order history (vault/orders.json.enc) for the admin page and a
     no-personal-data status file (ops/agent-status.json) that Business-Fox can read.

Secrets (GitHub > Settings > Secrets and variables > Actions):
  VAULT_KEY            base64 32-byte key (already set)
  SQUARE_ACCESS_TOKEN  Square production access token
  GMAIL_APP_PASSWORD   Google app password for the store Gmail
  ADMIN_PASSWORD       password for admin.html (12+ characters)

Usage:
  python tools/delivery_bot.py            normal run
  python tools/delivery_bot.py --setup-admin   (re)create admin login from ADMIN_PASSWORD
  python tools/delivery_bot.py --dry-run  do everything except send email / write files
"""
import base64
import email.utils
import hashlib
import imaplib
import json
import os
import re
import smtplib
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CFG = json.load(open("tools/delivery_bot.json", encoding="utf-8"))
DRY = "--dry-run" in sys.argv
NOW = datetime.now(timezone.utc)
SQUARE = "https://connect.squareup.com/v2"
SQUARE_VERSION = "2025-01-23"
ORDERS_FILE = "vault/orders.json.enc"
STATUS_FILE = "ops/bot-status.json"
AGENT_FILE = "ops/agent-status.json"
log_lines = []


def log(msg):
    print(msg)
    log_lines.append(msg)


# ------------------------------------------------------------------ crypto (matches admin.html)
def vault_key():
    raw = os.environ.get("VAULT_KEY", "").strip()
    if not raw:
        return None
    k = base64.b64decode(raw)
    assert len(k) == 32, "VAULT_KEY must be 32 bytes (base64)"
    return k


def enc(key, data: bytes, aad: bytes = None) -> bytes:
    iv = os.urandom(12)
    return iv + AESGCM(key).encrypt(iv, data, aad)


def dec(key, blob: bytes, aad: bytes = None) -> bytes:
    return AESGCM(key).decrypt(blob[:12], blob[12:], aad)


def setup_admin(key):
    pw = os.environ.get("ADMIN_PASSWORD", "")
    owner = CFG["owner_email"].strip().lower()
    if len(pw) < 12:
        log("ADMIN_PASSWORD missing or shorter than 12 characters - admin login not created.")
        return False
    salt = os.urandom(16)
    iters = 600_000
    kek = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iters).derive(pw.encode())
    iv = os.urandom(12)
    wrapped = AESGCM(kek).encrypt(iv, key, owner.encode())
    doc = {"v": 1, "kdf": "PBKDF2-SHA256", "iterations": iters,
           "salt": base64.b64encode(salt).decode(), "iv": base64.b64encode(iv).decode(),
           "wrapped_key": base64.b64encode(wrapped).decode(),
           "password_fingerprint": hashlib.sha256(salt + pw.encode()).hexdigest()[:16],
           "created": NOW.strftime("%Y-%m-%dT%H:%M:%SZ")}
    if not DRY:
        os.makedirs("vault", exist_ok=True)
        json.dump(doc, open("vault/admin.json", "w"), indent=2)
    log("Admin login created for " + owner)
    return True


def admin_needs_setup():
    pw = os.environ.get("ADMIN_PASSWORD", "")
    if not pw:
        return False
    if not os.path.exists("vault/admin.json"):
        return True
    doc = json.load(open("vault/admin.json"))
    fp = hashlib.sha256(base64.b64decode(doc["salt"]) + pw.encode()).hexdigest()[:16]
    return fp != doc.get("password_fingerprint")   # password secret was changed


# ------------------------------------------------------------------ square
def sq(method, path, body=None):
    token = os.environ["SQUARE_ACCESS_TOKEN"]
    req = urllib.request.Request(SQUARE + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {token}", "Square-Version": SQUARE_VERSION,
                                          "Content-Type": "application/json", "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(2 ** attempt * 3)
                continue
            raise RuntimeError(f"Square {method} {path} -> {e.code}: {e.read()[:300]!r}")


def list_payments(since):
    out, cursor = [], None
    while True:
        q = f"/payments?begin_time={since.strftime('%Y-%m-%dT%H:%M:%SZ')}&sort_order=ASC&limit=100"
        if cursor:
            q += f"&cursor={cursor}"
        r = sq("GET", q)
        out += r.get("payments", [])
        cursor = r.get("cursor")
        if not cursor:
            return out


def get_orders(ids):
    orders = {}
    ids = [i for i in ids if i]
    for i in range(0, len(ids), 100):
        r = sq("POST", "/orders/batch-retrieve", {"order_ids": ids[i:i + 100]})
        for o in r.get("orders", []):
            orders[o["id"]] = o
    return orders


def customer_email(cid, cache={}):
    if not cid:
        return None
    if cid not in cache:
        try:
            cache[cid] = sq("GET", f"/customers/{cid}").get("customer", {}).get("email_address")
        except Exception:
            cache[cid] = None
    return cache[cid]


def ensure_cash_app(checkout_urls):
    """Turn on Cash App Pay for every store payment link."""
    changed, total, cursor = 0, 0, None
    while True:
        r = sq("GET", "/online-checkout/payment-links?limit=100" + (f"&cursor={cursor}" if cursor else ""))
        for pl in r.get("payment_links", []):
            if pl.get("url") not in checkout_urls:
                continue
            total += 1
            opts = pl.get("checkout_options") or {}
            apm = opts.get("accepted_payment_methods") or {}
            if apm.get("cash_app_pay"):
                continue
            apm["cash_app_pay"] = True
            opts["accepted_payment_methods"] = apm
            if not DRY:
                sq("PUT", f"/online-checkout/payment-links/{pl['id']}",
                   {"payment_link": {"version": pl["version"], "checkout_options": opts}})
            changed += 1
        cursor = r.get("cursor")
        if not cursor:
            break
    return total, changed


# ------------------------------------------------------------------ products
STOP = set("a an and the for of to your with in on by pdf printable template local service business".split())


def words(s):
    return set(w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in STOP)


def load_products():
    cat = json.load(open("catalog.json"))
    files = json.load(open("vault/products.json")) if os.path.exists("vault/products.json") else {}
    prods = []
    for p in cat["products"]:
        p = dict(p)
        p["file"] = files.get(p.get("id") or "", {}).get("file")
        if (p.get("id") or "").startswith("BF-PRI"):
            p["kind"] = "printable"
        elif (p.get("id") or "").startswith("BF-WEB") or re.search(r"website|launch kit", p["title"], re.I):
            p["kind"] = "website"
        else:
            p["kind"] = "service"
        prods.append(p)
    return prods


def match_product(item, prods):
    name = " ".join(x for x in (item.get("name"), item.get("variation_name")) if x and x.lower() != "regular")
    manual = CFG.get("square_item_map", {})
    for key, slug in manual.items():
        if key.lower() == (item.get("name") or "").lower():
            return next((p for p in prods if p["slug"] == slug), None), 1.0
    price = (item.get("base_price_money") or {}).get("amount")
    best, score = None, 0.0
    w = words(name)
    for p in prods:
        pw = words(p["title"])
        if not w or not pw:
            continue
        s = len(w & pw) / len(w | pw)
        try:
            if price is not None and p.get("price") and round(float(p["price"].replace(",", "")) * 100) == price:
                s += 0.25
        except ValueError:
            pass
        if s > score:
            best, score = p, s
    return (best, score) if score >= CFG.get("match_threshold", 0.55) else (None, score)


# ------------------------------------------------------------------ gmail
def gmail_sent_to(addr, after):
    """Return subjects of mail sent to addr after the payment time, or None if Gmail is unavailable."""
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    if not pw:
        return None
    try:
        M = imaplib.IMAP4_SSL("imap.gmail.com")
        M.login(CFG["store_email"], pw.replace(" ", ""))
        M.select('"[Gmail]/All Mail"', readonly=True)
        q = f'in:sent to:{addr} after:{int(after.timestamp())}'
        typ, data = M.search(None, "X-GM-RAW", f'"{q}"')
        ids = data[0].split() if typ == "OK" and data and data[0] else []
        subjects = []
        for i in ids[-5:]:
            t, d = M.fetch(i, "(BODY.PEEK[HEADER.FIELDS (SUBJECT)])")
            if t == "OK" and d and d[0]:
                subjects.append(d[0][1].decode(errors="ignore").replace("Subject:", "").strip())
        M.logout()
        return subjects
    except Exception as e:
        log(f"Gmail check failed: {e}")
        return None


WEBSITE_DONE = re.compile(r"^\s*(Delivered|Revised):\s*your website", re.I)


def website_delivered(subjects):
    return [x for x in (subjects or []) if WEBSITE_DONE.search(x)]


def send_mail(to, subject, text, html=None, attachment=None, attachment_name=None):
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    if not pw:
        raise RuntimeError("GMAIL_APP_PASSWORD is not set")
    msg = EmailMessage()
    msg["From"] = email.utils.formataddr((CFG["store_name"], CFG["store_email"]))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Reply-To"] = CFG["store_email"]
    msg["X-Business-Fox-Bot"] = "backup-delivery"
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")
    if attachment:
        msg.add_attachment(attachment, maintype="application", subtype="pdf", filename=attachment_name)
    if DRY:
        log(f"[dry-run] would email {to}: {subject}")
        return
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as s:
        s.login(CFG["store_email"], pw.replace(" ", ""))
        s.send_message(msg)


def deliver(order, product, key):
    first = (order.get("buyer_name") or "").split(" ")[0] or "there"
    title = product["title"]
    sig = f"\n\nThanks again,\n{CFG['store_name']}\n{CFG['store_url']}\n"
    if product["kind"] == "printable" and product.get("file"):
        pdf = dec(key, open(product["file"], "rb").read())
        text = (f"Hi {first},\n\nThank you for your order. Your {title} is attached to this email as a PDF.\n\n"
                "Print it at home on US Letter paper as often as you like (personal-use licence).\n"
                "If anything looks wrong or the attachment won't open, just reply to this email and we'll sort it out." + sig)
        fname = re.sub(r"[^A-Za-z0-9 \-]", "", title).strip() + ".pdf"
        send_mail(order["email"], f"Your Business Fox download: {title}", text, attachment=pdf, attachment_name=fname)
        return "file_sent"
    text = (f"Hi {first},\n\nThank you for ordering {title}. Your payment is confirmed.\n\n"
            "To get started, please reply to this email with:\n"
            "  1. Your business name and website or social links (if any)\n"
            "  2. What you offer and who your ideal customers are\n"
            "  3. Anything you want included, avoided, or matched (tone, examples, deadlines)\n\n"
            "Your delivery time starts as soon as we receive your brief, and you get one free revision." + sig)
    send_mail(order["email"], f"Your Business Fox order: {title} - next step", text)
    return "brief_request_sent"


def alert_owner(subject, lines):
    if not CFG.get("owner_alerts", True):
        return
    try:
        send_mail(CFG["owner_email"], f"[Business Fox bot] {subject}", "\n".join(lines) +
                  f"\n\nOpen the admin page: {CFG['store_url']}admin.html\n")
    except Exception as e:
        log(f"Owner alert failed: {e}")


# ------------------------------------------------------------------ state
def load_state(key):
    if os.path.exists(ORDERS_FILE):
        return json.loads(dec(key, open(ORDERS_FILE, "rb").read(), b"orders"))
    return {"orders": {}, "initialized": None}


def save_state(key, state):
    data = json.dumps(state, indent=1, sort_keys=True).encode()
    if os.path.exists(ORDERS_FILE):
        try:
            if dec(key, open(ORDERS_FILE, "rb").read(), b"orders") == data:
                return False
        except Exception:
            pass
    if not DRY:
        os.makedirs("vault", exist_ok=True)
        open(ORDERS_FILE, "wb").write(enc(key, data, b"orders"))
    return True


def write_json_if_changed(path, doc, ignore=("checked",)):
    old = json.load(open(path)) if os.path.exists(path) else None
    strip = lambda d: {k: v for k, v in (d or {}).items() if k not in ignore}
    if strip(old) == strip(doc):
        return False
    if not DRY:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(doc, open(path, "w"), indent=2)
    return True


# ------------------------------------------------------------------ main
def main():
    key = vault_key()
    missing = [s for s in ("VAULT_KEY", "SQUARE_ACCESS_TOKEN", "GMAIL_APP_PASSWORD") if not os.environ.get(s)]
    status = json.load(open(STATUS_FILE)) if os.path.exists(STATUS_FILE) else {}
    status.update({"missing_secrets": missing, "checked": NOW.strftime("%Y-%m-%dT%H:%M:%SZ")})
    if not key:
        log("VAULT_KEY is not set; nothing can run.")
        write_json_if_changed(STATUS_FILE, status)
        return
    if "--setup-admin" in sys.argv or admin_needs_setup():
        setup_admin(key)
    status["admin_ready"] = os.path.exists("vault/admin.json")

    if "SQUARE_ACCESS_TOKEN" in missing:
        log("Waiting for SQUARE_ACCESS_TOKEN.")
        write_json_if_changed(STATUS_FILE, status)
        return

    prods = load_products()
    if CFG.get("enable_cash_app_pay", True):
        try:
            total, changed = ensure_cash_app({p["checkout"] for p in prods})
            status["cash_app_pay"] = {"links": total, "ok": True}
            if changed:
                log(f"Turned on Cash App Pay for {changed} payment link(s)")
        except Exception as e:
            status["cash_app_pay"] = {"ok": False, "error": str(e)[:200]}
            log(f"Cash App Pay check failed: {e}")

    state = load_state(key)
    first_run = not state.get("initialized")
    since = NOW - timedelta(days=CFG.get("history_days_first_run", 30) if first_run else CFG.get("lookback_days", 3))
    payments = list_payments(since)
    orders = get_orders([p.get("order_id") for p in payments])
    grace = timedelta(minutes=CFG.get("grace_minutes", 30))
    max_age = timedelta(hours=CFG.get("max_auto_send_hours", 72))
    acted = []

    ignore = CFG.get("ignore_payment_ids", {})
    for pid in list(state["orders"]):
        if pid in ignore:
            state["orders"].pop(pid)
    for pay in payments:
        pid = pay["id"]
        if pid in ignore:
            continue
        rec = state["orders"].get(pid)
        paid = pay.get("status") == "COMPLETED"
        refunded = (pay.get("refunded_money") or {}).get("amount", 0) >= (pay.get("amount_money") or {}).get("amount", 1)
        if rec and rec["status"] in ("delivered_by_ai", "delivered_by_bot", "manual_done", "website_in_progress"):
            if refunded and rec.get("payment_status") != "REFUNDED":
                rec["payment_status"] = "REFUNDED"
            continue
        o = orders.get(pay.get("order_id"), {})
        wallet = (pay.get("wallet_details") or {}).get("brand")
        method = "Cash App Pay" if wallet == "CASH_APP" or pay.get("source_type") == "CASH_APP" else \
                 (wallet.replace("_", " ").title() if wallet else (pay.get("card_details", {}).get("card", {}).get("card_brand") or pay.get("source_type", "")).title())
        recipient = {}
        for f in o.get("fulfillments", []):
            for k in ("shipment_details", "pickup_details", "delivery_details", "digital_details"):
                recipient = (f.get(k) or {}).get("recipient") or recipient
        buyer_email = (pay.get("buyer_email_address") or recipient.get("email_address")
                       or customer_email(pay.get("customer_id") or o.get("customer_id")))
        items = []
        for li in o.get("line_items", []) or [{"name": pay.get("note") or "", "base_price_money": pay.get("amount_money")}]:
            prod, score = match_product(li, prods)
            items.append({"square_name": li.get("name"), "qty": li.get("quantity", "1"),
                          "product_slug": prod["slug"] if prod else None, "product_id": prod.get("id") if prod else None,
                          "product_title": prod["title"] if prod else None, "kind": prod["kind"] if prod else None,
                          "match": round(score, 2)})
        created = datetime.strptime(pay["created_at"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        rec = rec or {"payment_id": pid, "order_id": pay.get("order_id"), "paid_at": pay["created_at"],
                      "history": []}
        rec.update({"email": buyer_email, "buyer_name": recipient.get("display_name") or
                    " ".join(x for x in ((pay.get("billing_address") or {}).get("first_name"), (pay.get("billing_address") or {}).get("last_name")) if x),
                    "amount": (pay.get("amount_money") or {}).get("amount", 0) / 100,
                    "currency": (pay.get("amount_money") or {}).get("currency", "USD"),
                    "method": method, "payment_status": "REFUNDED" if refunded else pay.get("status"),
                    "receipt_url": pay.get("receipt_url"), "items": items})
        state["orders"][pid] = rec

        def mark(st, note):
            if rec.get("status") != st or (rec["history"] and rec["history"][-1]["note"] != note):
                rec["history"].append({"at": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"), "status": st, "note": note})
            rec["status"] = st

        if not paid or refunded:
            mark("not_paid", f"Payment status {rec['payment_status']} - nothing will be sent until it is COMPLETED")
            continue
        if not buyer_email:
            if rec.get("status") != "needs_review":
                acted.append(f"No buyer email on payment {pid} ({rec['amount']:.2f})")
            mark("needs_review", "No buyer email on the Square payment")
            continue
        if any(not it["product_slug"] for it in items):
            if rec.get("status") != "needs_review":
                acted.append(f"Could not match '{', '.join(i['square_name'] or '?' for i in items)}' to a store product")
            mark("needs_review", "Could not match the Square item to a store product. Add it to square_item_map.")
            continue
        if NOW - created < grace:
            mark("waiting_for_ai", f"Giving Business-Fox until {(created + grace).strftime('%H:%M UTC')} to deliver")
            continue
        sent = gmail_sent_to(buyer_email, created)
        is_web = any(it["kind"] == "website" for it in items)
        if is_web and website_delivered(sent):
            mark("delivered_by_ai", "Website delivered: " + "; ".join(website_delivered(sent))[:200])
            continue
        if is_web and sent:
            rec["website_pending"] = True
            mark("website_in_progress", "Business-Fox sent the questionnaire. Waiting for the buyer's answers, the build and your approval.")
            continue
        if sent:
            mark("delivered_by_ai", "Found email to buyer after payment: " + "; ".join(sent)[:200])
            continue
        if sent is None and not CFG.get("send_if_gmail_unavailable", True):
            mark("needs_review", "Could not check Gmail Sent folder")
            continue
        if (first_run and NOW - created > timedelta(hours=24)) or NOW - created > max_age:
            if rec.get("status") != "needs_review":
                acted.append(f"Old undelivered order for {buyer_email}: {', '.join(i['product_title'] for i in items)}")
            mark("needs_review", "Older order with no delivery email found - not auto-sent. Deliver manually from the admin page.")
            continue
        if rec.get("attempts", 0) >= 3:
            mark("needs_review", "Bot could not send after 3 tries - deliver manually from the admin page.")
            continue
        results = []
        try:
            for it in items:
                prod = next(p for p in prods if p["slug"] == it["product_slug"])
                results.append(deliver(rec, prod, key))
            needs_work = any(r == "brief_request_sent" for r in results)
            if is_web:
                rec["website_pending"] = True
                mark("website_in_progress", "Bot sent the questionnaire because Business-Fox hadn't. Waiting for the build and your approval.")
            else:
                mark("delivered_by_bot", ("Bot emailed " + ", ".join(results)) +
                     (" - service work still needs to be done" if needs_work else ""))
                rec["service_pending"] = needs_work
            acted.append(f"Backup delivery to {buyer_email}: {', '.join(i['product_title'] for i in items)} ({', '.join(results)})")
        except Exception as e:
            rec["attempts"] = rec.get("attempts", 0) + 1
            mark("delivery_failed", f"Send failed (try {rec['attempts']}/3): {e}"[:300])
            acted.append(f"FAILED delivery to {buyer_email} (try {rec['attempts']}/3): {e}")

    # websites stay "in progress" until the finished site email ("Delivered: your website ...") is in Sent mail
    for rec in state["orders"].values():
        if rec.get("status") != "website_in_progress" or not rec.get("email"):
            continue
        paid_dt = datetime.strptime(rec["paid_at"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        done = website_delivered(gmail_sent_to(rec["email"], paid_dt))
        if done:
            rec["website_pending"] = False
            rec["status"] = "delivered_by_ai"
            rec["history"].append({"at": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"), "status": "delivered_by_ai",
                                   "note": "Website approved and delivered: " + "; ".join(done)[:200]})
            acted.append(f"Website delivered to {rec['email']}")
        elif NOW - paid_dt > timedelta(days=CFG.get("website_overdue_days", 9)) and not rec.get("overdue_alerted"):
            rec["overdue_alerted"] = True
            acted.append(f"Website for {rec['email']} is past {CFG.get('website_overdue_days', 9)} days and not delivered. "
                         "Check Business-Fox (is the PC on? is it waiting for 'approve N'?).")

    state["initialized"] = state.get("initialized") or NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
    changed = save_state(key, state)

    # public, no personal data - Business-Fox can read this to stay in sync
    counts = {}
    for r in state["orders"].values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    agent = {
        "_readme": "Written by the backup delivery bot. No personal data. Business-Fox: treat orders marked "
                   "delivered_by_bot as already delivered (do not email them again). website_in_progress means the questionnaire "
                   "went out and the site must still be built and approved. service_pending=true means the "
                   "custom work still has to be done once the buyer sends their brief.",
        "checked": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "counts": counts,
        "orders": sorted([{"ref": hashlib.sha256(r["payment_id"].encode()).hexdigest()[:12], "paid_at": r["paid_at"],
                           "products": [i["product_slug"] for i in r["items"]], "status": r["status"],
                           "service_pending": r.get("service_pending", False),
                           "website_pending": r.get("website_pending", False), "method": r.get("method")}
                          for r in state["orders"].values()], key=lambda x: x["paid_at"], reverse=True)[:200],
    }
    write_json_if_changed(AGENT_FILE, agent)
    status["last_order_check_ok"] = True
    write_json_if_changed(STATUS_FILE, status)

    if acted:
        alert_owner(f"{len(acted)} order update(s)", acted)
    log(f"Checked {len(payments)} payment(s); state {'changed' if changed else 'unchanged'}; {len(acted)} action(s)")


if __name__ == "__main__":
    main()
