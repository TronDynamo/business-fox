#!/usr/bin/env python3
"""Create Square payment links (card, Apple Pay, Google Pay, Cash App Pay) for tools/new_products.json items that don't have one yet."""
import json, os, urllib.request

TOKEN = os.environ["SQUARE_ACCESS_TOKEN"]
H = {"Authorization": "Bearer " + TOKEN, "Square-Version": "2025-01-23", "Content-Type": "application/json"}

def sq(method, path, body=None):
    r = urllib.request.Request("https://connect.squareup.com/v2" + path, method=method, headers=H,
                               data=json.dumps(body).encode() if body is not None else None)
    return json.loads(urllib.request.urlopen(r, timeout=60).read() or b"{}")

cfg = json.load(open("tools/new_products.json"))
loc = [l for l in sq("GET", "/locations")["locations"] if l.get("status") == "ACTIVE"][0]["id"]
links = sq("GET", "/online-checkout/payment-links?limit=100").get("payment_links", [])
template = next((l.get("checkout_options", {}) for l in links if l.get("checkout_options")), {})
made = 0
for p in cfg["products"]:
    if p.get("square_url"):
        continue
    opts = {"accepted_payment_methods": {"apple_pay": True, "google_pay": True, "cash_app_pay": True}, "ask_for_shipping_address": False}
    if template.get("redirect_url"):
        opts["redirect_url"] = template["redirect_url"]
    if template.get("merchant_support_email"):
        opts["merchant_support_email"] = template["merchant_support_email"]
    res = sq("POST", "/online-checkout/payment-links", {
        "idempotency_key": "bf-new-" + p["id"],
        "quick_pay": {"name": p["title"], "price_money": {"amount": p["price_cents"], "currency": "USD"}, "location_id": loc},
        "checkout_options": opts,
        "description": p["short"][:250]})
    pl = res["payment_link"]
    p["square_url"], p["square_link_id"] = pl["url"], pl["id"]
    made += 1
    print("Created link for", p["title"])
json.dump(cfg, open("tools/new_products.json", "w"), indent=2)
print(made, "link(s) created")
