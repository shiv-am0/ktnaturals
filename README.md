# KT Naturals — Phase 1 catalogue

A server-rendered Django 5.2 site for browsing products and preparing WhatsApp enquiries. It does not accept payment, submit an order, or send a WhatsApp message. The customer opens a prefilled message and chooses whether to send it; the owner confirms availability, final price, delivery charges and payment. The WhatsApp number and all real business claims/content must come from the owner.

## Run locally

Python 3.13 (or another Python version supported by Django 5.2), `uv`, and a writable local directory are required. From this repository directory:

```sh
uv venv --python 3.13
uv pip install -r requirements.txt
cp .env.example .env
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Edit `.env` for your machine. Never use its local example secret in production. Enter a unique owner username and password interactively; never put the password in source or shell history. Owner login: `http://127.0.0.1:8000/owner/login/`. To reset: `.venv/bin/python manage.py changepassword USERNAME` (interactive); signed-in staff can change their own password under Owner studio → Change password. A staff-only non-superuser may also use the custom owner area; only trusted superusers should use `/admin/` maintenance fallback. There is no public registration. `manage.py migrate` creates local `data/db.sqlite3`; media is stored in `media/`. Both are ignored by Git. For an empty site, pages render without contact details or products.

To see *explicitly fictional local examples* only:

```sh
.venv/bin/python manage.py seed_demo --confirm-local
```

This command requires DEBUG=true, creates six products labelled “Demo”, includes original illustrated placeholder images marked “not actual packaging”, and does not overwrite existing slugs on subsequent runs. It does not set a WhatsApp number or real owner information. Never copy the local database or media into production, and do not present demo products to real customers. Start production with an empty database and owner-approved real data. The command refuses to run with DEBUG=false.

The current local database instead contains the owner-PDF catalogue: 18 products and 61 pack-size prices, with the former six demo products removed. `CATALOGUE_IMPORT.md` records exact source pages, missing photos, a price discrepancy requiring confirmation, rollback snapshot and the idempotent import command. For a fresh database, `manage.py import_catalogue --apply` creates drafts; `--publish-local` and `--replace-demo-local` are explicitly restricted to a localhost DEBUG preview. All currently visible product cover images say “OWNER PHOTO PENDING”; replace them before launch. The original PDF is excluded from Git and Docker because it contains unrelated payment details.

## Owner workflow

See `OWNER_GUIDE.md` for the mobile editing sequence. Create a category (optional), save a product as Draft, add at least one active priced size and a cover photo with alt text, then change status to Published. Edits are reflected in the public catalogue. Archived and draft products are hidden from public URLs/search/sitemap; private previews require staff login. Don't remove the last active size or cover from a published product; move it to Draft first. The owner can manage homepage copy, contact methods and information pages at `/owner/settings/`. The supplied catalogue story is published locally; delivery/returns and privacy remain draft until the owner supplies and approves them. Without a configured validated WhatsApp number the enquiry button is unavailable and visitors see a contact state. Product enquiry price always comes from the server, not the browser. If a product/variant/contact changed since the page loaded the customer reviews fresh information before proceeding.

## Verification

```sh
DJANGO_DEBUG=true .venv/bin/python manage.py check
DJANGO_DEBUG=true .venv/bin/python manage.py test
DJANGO_DEBUG=true .venv/bin/python -m unittest deploy.test_backup_wrapper
DJANGO_DEBUG=true .venv/bin/python qa/check_seo.py
DJANGO_DEBUG=true .venv/bin/python qa/verify_catalogue_import.py
```

For local Chromium screenshots, accessibility audits and owner-flow tests (after installing/running the server as above):

```sh
curl -fsSL https://cdn.jsdelivr.net/npm/axe-core@4.10.3/axe.min.js -o /tmp/ktnaturals-axe.min.js
uv run --with playwright --python .venv/bin/python python qa/browser_audit.py --axe-script /tmp/ktnaturals-axe.min.js
DJANGO_DEBUG=true uv run --with playwright --python .venv/bin/python python qa/owner_flow.py
```

These browser checks use local data and write ignored screenshots under `qa/evidence/`. The owner script creates and removes a disposable staff account/category/product. Never send a WhatsApp message during QA. The SEO script checks the current database; run `seed_demo` locally to include representative product pages. `qa/test_rclone_filters.py` requires Docker, downloads a pinned rclone image and tests only local-to-local transfer of hidden media. `qa/container_smoke.py` requires an image built as `ktnaturals:local-verification` and creates/removes only its own temporary Docker volume/container; no public deploy.

## Deployment and launch

`OPERATIONS.md` gives exact Docker Compose/Caddy HTTPS deployment, UID/mount permissions, SQLite+media backups, scheduled off-server transfer, restore drill and future PostgreSQL migration. `SEO_LAUNCH.md` gives domain/Search Console and Google rich-results validation steps. Do **not** deploy until owner approval, real domain/contact/products/photographs and policy text are available. Django/Caddy configuration does not make hosting, domain or external backup storage free. A persistent volume by itself is not a backup.

Architecture: one Django/Gunicorn process on a Linux server, SQLite on local persistent disk, Caddy serving collected static assets and validated uploaded images. The catalogue stores Category → Product → priced ProductVariant and ProductImage; SiteSettings holds contact and copy. Django forms/auth/CSRF/sessions and django-axes protect the custom `/owner/` UI; Pillow validates and re-encodes JPEG/PNG/WebP uploads. No SPA, separate API, managed database, checkout or order record.
