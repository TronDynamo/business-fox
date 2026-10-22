# Rules for Business-Fox (read before every publish)

These rules keep the store clean. The Site Doctor (`tools/site_doctor.py`) runs automatically
after every push and enforces them, so anything that breaks them gets undone. Follow them and
your work sticks.

## Before creating a product or guide

1. Download and read `catalog.json` from the repo (live products, live guides, retired pages):
   https://raw.githubusercontent.com/TronDynamo/business-fox/main/catalog.json
2. Do NOT create a new page if a product or guide with a similar name already exists.
   Update the existing page instead (same slug, same Square link).
3. Never reuse or recreate a slug listed under `retired_pages`. Those pages are redirects.
4. One Square checkout link = one product. Never put the same Square link on two pages.
5. Product names must be unique. If two versions are really different, put the difference in
   the name (for example "Contractor monthly content bundle" vs
   "Local service business monthly content bundle").
6. Guides: at most one guide per topic. Before writing, check `catalog.json` guides for the same
   topic (product descriptions, return policy, about page, newsletters, operations, and so on).

## When publishing

- Contact email on every page: **godzilla9zjb@gmail.com**. Never use artipixel99@gmail.com.
- In `feed.xml` and `merchant.xml`, every item's link must be that product's own page
  (`https://trondynamo.github.io/business-fox/<slug>.html`), never the homepage.
- `sitemap.xml` is rebuilt automatically. You can still update it, but the Site Doctor's
  version wins.
- Pages marked `noindex` (for example the portfolio samples) stay out of the sitemap.

## After publishing

- Run `python tools/site_doctor.py --check` from a local copy of the repo. Exit code 0 means
  clean. Exit code 1 lists the problems; fix them or let the automatic run fix them.
- Read `SITE_REPORT.md` for what the last automatic run changed.

## Store owner overrides (`tools/site_doctor.json`)

- `renames`: forced product names, applied on every run.
- `redirects`: retired page -> replacement page. New duplicates are added here automatically.
- `not_duplicates`: list of `[slug_a, slug_b]` pairs that look alike but are intentionally separate.
- `banned_emails`: addresses that get replaced with `contact_email`.
