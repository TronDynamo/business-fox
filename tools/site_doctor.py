#!/usr/bin/env python3
"""Business Fox Site Doctor.

Checks the store for the problems that keep showing up and repairs them:
  * duplicate products (same name or same Square checkout link)
  * duplicate / near-duplicate guides
  * banned contact emails (e.g. the old ArtiPixel address)
  * feed.xml / merchant.xml items that link to the homepage instead of the product
  * sitemap.xml missing pages, or listing redirected pages
  * broken internal links (reported only)

It also writes catalog.json, the single list of live products and guides that
Business-Fox must read before creating anything new.

Usage:
  python tools/site_doctor.py          # fix everything, write SITE_REPORT.md + catalog.json
  python tools/site_doctor.py --check  # change nothing; exit 1 if any problem is found

Only the Python standard library is used. Rules live in tools/site_doctor.json.
"""
import glob
import html
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CFG_PATH = "tools/site_doctor.json"
CFG = json.load(open(CFG_PATH, encoding="utf-8"))
BASE = CFG["base_url"].rstrip("/") + "/"
HOME = BASE.rstrip("/")
CHECK = "--check" in sys.argv

STOP = set("a an and the for of to your you with without in on by from how pdf printable "
           "template templates set pack kit sheet guide practical simple local service "
           "business businesses small step steps".split())
SKIP_PAGES = {"index.html", "about.html", "guides.html", "portfolio.html", "business-fox.html"}

changes, problems = [], []
_files = {}


def read(path):
    if path not in _files:
        _files[path] = open(path, encoding="utf-8", errors="ignore").read()
    return _files[path]


def write(path, text):
    if read(path) != text:
        _files[path] = text
        if not CHECK:
            open(path, "w", encoding="utf-8").write(text)
        return True
    return False


def is_stub(text):
    return 'http-equiv="refresh"' in text[:2000]


def h1(text):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


def words(title):
    return [w for w in re.findall(r"[a-z0-9]+", title.lower()) if w not in STOP]


def created(path, _cache={}):
    """When the page first appeared in git (older pages win duplicate fights)."""
    if path not in _cache:
        import subprocess
        try:
            out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%ct", "--", path],
                                 capture_output=True, text=True, timeout=30).stdout.split()
            _cache[path] = int(out[-1]) if out else 10**12
        except Exception:
            _cache[path] = 10**12
    return _cache[path]


def num(slug):
    m = re.search(r"-(\d+)\.html$", slug)
    return int(m.group(1)) if m else 0


def stub_html(target):
    title = target
    if os.path.exists(target):
        m = re.search(r"<title>([^<]*)", read(target))
        if m:
            title = m.group(1)
    t = html.escape(html.unescape(title))
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{t}</title>\n'
            f'<meta name="robots" content="noindex,follow"><link rel="canonical" href="{BASE}{target}">\n'
            f'<meta http-equiv="refresh" content="0; url={target}"></head>\n'
            f'<body><p>This page has moved to <a href="{target}">{t}</a>.</p>'
            f'<script>location.replace("{target}")</script></body></html>\n')


def listing_pages():
    return ["index.html", "guides.html"] + sorted(glob.glob("c-*.html"))


# ---------------------------------------------------------------- 1. emails
def fix_emails():
    targets = [f for f in glob.glob("*.html") + glob.glob("*.xml") + glob.glob("*.txt")]
    for bad in CFG["banned_emails"]:
        for f in targets:
            s = read(f)
            if bad in s:
                problems.append(f"Banned email {bad} found in {f}")
                if write(f, s.replace(bad, CFG["contact_email"])):
                    changes.append(f"Replaced {bad} with {CFG['contact_email']} in {f}")


# ---------------------------------------------------------------- 2. inventory
def inventory():
    products, guides = {}, {}
    for f in sorted(glob.glob("*.html")):
        if f in SKIP_PAGES or f.startswith(("c-", "google")):
            continue
        s = read(f)
        if is_stub(s):
            continue
        if f.startswith("guide-"):
            guides[f] = {"slug": f, "title": h1(s)}
            continue
        sq = re.findall(r"https://square\.link/u/[A-Za-z0-9]+", s)
        if not sq:
            continue
        og = re.search(r'og:image" content="[^"]*/(BF-[A-Z]+-[0-9A-F]+)-cover', s)
        price = re.search(r'class="price">\$?([0-9.,]+)', s) or re.search(r"\$([0-9]+\.[0-9]{2})", s)
        products[f] = {
            "slug": f,
            "id": og.group(1) if og else None,
            "title": h1(s),
            "price": price.group(1) if price else None,
            "checkout": sq[0],
            "listed": f'href="{f}"' in read("index.html"),
        }
    return products, guides


# ---------------------------------------------------------------- 3. redirects
def remove_from_listings(slug):
    e = re.escape(slug)
    pats = [
        rf'<a class="card" href="{e}"[^>]*>.*?</div></a>',                 # product cards
        rf'<h2><a href="{e}">.*?</a></h2>\s*<p>.*?</p>',                   # guide list entries
        rf',?\{{"@type":"Offer"[^{{}}]*?/{e}"\}}',                          # JSON-LD offers
    ]
    for f in listing_pages():
        s = read(f)
        new = s
        for p in pats:
            new = re.sub(p, "", new, flags=re.S)
        new = new.replace('"offers":[,', '"offers":[')
        if write(f, new):
            changes.append(f"Removed {slug} from {f}")
    for f in ("feed.xml", "merchant.xml"):
        if os.path.exists(f):
            s = read(f)
            new = re.sub(rf"<item>(?:(?!</item>).)*?/{e}<(?:(?!</item>).)*</item>", "", s, flags=re.S)
            if write(f, new):
                changes.append(f"Removed {slug} from {f}")


def enforce_redirects():
    for old, new in CFG["redirects"].items():
        if not os.path.exists(new):
            problems.append(f"Redirect target missing: {old} -> {new}")
            continue
        if os.path.exists(old) and not is_stub(read(old)):
            problems.append(f"{old} was recreated even though it redirects to {new}")
            write(old, stub_html(new))
            changes.append(f"Turned {old} back into a redirect to {new}")
        elif not os.path.exists(old):
            write(old, stub_html(new))
        remove_from_listings(old)


def add_redirect(old, new, why):
    problems.append(f"Duplicate: {old} duplicates {new} ({why})")
    CFG["redirects"][old] = new
    write(old, stub_html(new))
    remove_from_listings(old)
    changes.append(f"Redirected duplicate {old} -> {new}")


# ---------------------------------------------------------------- 4. renames
def apply_renames(products):
    for slug, name in CFG["renames"].items():
        if slug not in products:
            continue
        e = re.escape(slug)
        old = products[slug]["title"]
        if old and old != name:
            s = read(slug)
            write(slug, re.sub(r"(<h1[^>]*>).*?(</h1>)", lambda m: m.group(1) + html.escape(name) + m.group(2), s, count=1, flags=re.S))
        blocks = [rf'<a class="card" href="{e}"[^>]*>.*?</div></a>',
                  rf'\{{"@type":"Offer"[^{{}}]*?/{e}"\}}',
                  rf"<item>(?:(?!</item>).)*?/{e}<(?:(?!</item>).)*</item>"]
        for f in listing_pages() + ["feed.xml", "merchant.xml"]:
            if not os.path.exists(f):
                continue
            s = read(f)

            def swap(m):
                b = m.group(0)
                cur = (re.search(r"<strong>(.*?)</strong>", b) or re.search(r'"name":"(.*?)"', b)
                       or re.search(r"<g:title>(.*?)</g:title>", b) or re.search(r"<title>(.*?)</title>", b))
                return b.replace(cur.group(1), name) if cur and cur.group(1) != name else b
            new = s
            for p in blocks:
                new = re.sub(p, swap, new, flags=re.S)
            if write(f, new):
                changes.append(f"Applied name '{name}' for {slug} in {f}")
        products[slug]["title"] = name


# ---------------------------------------------------------------- 5. duplicates
def dedupe_products(products):
    allowed = {tuple(sorted(p)) for p in CFG["not_duplicates"]}
    groups = {}
    for p in products.values():
        groups.setdefault(" ".join(words(p["title"])), []).append(p)
        groups.setdefault(p["checkout"], []).append(p)
    seen = set()
    for key, grp in groups.items():
        grp = [g for g in grp if g["slug"] in products]
        if len(grp) < 2 or not key:
            continue
        # keep: listed on the homepage first, then the original (oldest, lowest number)
        grp.sort(key=lambda g: (not g["listed"], created(g["slug"]), num(g["slug"])))
        keep = grp[0]
        for d in grp[1:]:
            if d["slug"] in seen or tuple(sorted((keep["slug"], d["slug"]))) in allowed:
                continue
            seen.add(d["slug"])
            why = "same checkout link" if key.startswith("https://") else f"same name '{d['title']}'"
            add_redirect(d["slug"], keep["slug"], why)
            products.pop(d["slug"], None)


def dedupe_guides(guides):
    listed = read("guides.html")
    order = sorted(guides.values(), key=lambda g: (f'href="{g["slug"]}"' not in listed,
                                                   created(g["slug"]), g["slug"]))
    kept = []
    thr = CFG.get("guide_similarity_threshold", 0.6)
    allowed = {tuple(sorted(p)) for p in CFG["not_duplicates"]}
    for g in order:
        w = set(words(g["title"]))
        match = None
        for k in kept:
            kw = set(words(k["title"]))
            if w and kw and len(w & kw) / len(w | kw) >= thr and tuple(sorted((g["slug"], k["slug"]))) not in allowed:
                match = k
                break
        if match:
            add_redirect(g["slug"], match["slug"], f"near-identical title '{g['title']}'")
            guides.pop(g["slug"])
        else:
            kept.append(g)


# ---------------------------------------------------------------- 6. feeds
def fix_feeds(products):
    by_id = {p["id"]: p["slug"] for p in products.values() if p["id"]}
    for f, link_tag, id_tag in (("feed.xml", "link", "guid"), ("merchant.xml", "g:link", "g:id")):
        if not os.path.exists(f):
            continue
        s = read(f)

        def fix(m):
            item = m.group(0)
            pid = re.search(rf"<{id_tag}>([^<]+)</{id_tag}>", item)
            link = re.search(rf"<{link_tag}>([^<]*)</{link_tag}>", item)
            if not pid or not link:
                return item
            slug = by_id.get(pid.group(1).strip())
            target = BASE + slug if slug else None
            cur = link.group(1).strip()
            ok = cur.startswith(BASE) and os.path.exists(cur[len(BASE):].split("?")[0] or "index.html") and cur.rstrip("/") != HOME
            if target and cur != target and not ok:
                problems.append(f"{f}: item {pid.group(1)} linked to {cur}")
                return item.replace(link.group(0), f"<{link_tag}>{target}</{link_tag}>")
            return item
        new = re.sub(r"<item>.*?</item>", fix, s, flags=re.S)
        if write(f, new):
            changes.append(f"Fixed product links in {f}")


# ---------------------------------------------------------------- 7. sitemap
def rebuild_sitemap():
    pages = []
    for f in sorted(glob.glob("*.html")) + sorted(glob.glob("portfolio/*/index.html")):
        if f.startswith("google"):
            continue
        s = read(f)
        if is_stub(s) or re.search(r'name="robots" content="[^"]*noindex', s):
            continue
        pages.append(BASE if f == "index.html" else BASE + f)
    pages.sort(key=lambda u: (u != BASE, u))
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           + "".join(f"<url><loc>{u}</loc></url>" for u in pages) + "</urlset>\n")
    old = read("sitemap.xml") if os.path.exists("sitemap.xml") else ""
    if set(re.findall(r"<loc>([^<]+)</loc>", old)) != set(pages):
        problems.append("sitemap.xml was out of date")
        write("sitemap.xml", xml)
        changes.append(f"Rebuilt sitemap.xml ({len(pages)} pages)")


# ---------------------------------------------------------------- 8. links
def check_links():
    broken = []
    for f in glob.glob("*.html") + glob.glob("portfolio/**/*.html", recursive=True):
        for m in re.findall(r'(?:href|src)="([^"#?]+)', read(f)):
            if re.match(r"^(https?:|mailto:|tel:|data:|javascript:|//)", m):
                continue
            p = os.path.normpath(os.path.join(os.path.dirname(f), m))
            if m.endswith("/"):
                p = os.path.join(p, "index.html")
            if not os.path.exists(p):
                broken.append(f"{f} -> {m}")
    for b in sorted(set(broken)):
        problems.append(f"Broken link: {b}")
    return broken


# ---------------------------------------------------------------- main
def main():
    fix_emails()
    enforce_redirects()
    products, guides = inventory()
    apply_renames(products)
    dedupe_products(products)
    dedupe_guides(guides)
    fix_feeds(products)
    rebuild_sitemap()
    check_links()

    if not CHECK:
        json.dump(CFG, open(CFG_PATH, "w", encoding="utf-8"), indent=2)
        catalog = {
            "_readme": "Live Business Fox catalog. Business-Fox: read this BEFORE creating a product or guide. "
                       "If something with a similar name already exists, update that page instead of making a new one. "
                       "Never reuse a slug listed in 'retired_pages'.",
            "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "contact_email": CFG["contact_email"],
            "products": sorted(products.values(), key=lambda p: num(p["slug"])),
            "guides": sorted(guides.values(), key=lambda g: g["slug"]),
            "retired_pages": CFG["redirects"],
        }
        open("catalog.json", "w", encoding="utf-8").write(json.dumps(catalog, indent=2) + "\n")
        report = ["# Site Doctor report", "", f"Run: {catalog['updated']}", "",
                  f"Live products: {len(products)}  |  Live guides: {len(guides)}  |  Redirected pages: {len(CFG['redirects'])}", "",
                  "## Fixed this run", ""] + [f"- {c}" for c in changes or ["Nothing needed fixing."]] + \
                 ["", "## Problems found", ""] + [f"- {p}" for p in problems or ["None."]]
        open("SITE_REPORT.md", "w", encoding="utf-8").write("\n".join(report) + "\n")

    print(f"{len(problems)} problem(s), {len(changes)} fix(es)")
    for p in problems:
        print("  PROBLEM:", p)
    for c in changes:
        print("  FIXED:  ", c)
    if CHECK and problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
