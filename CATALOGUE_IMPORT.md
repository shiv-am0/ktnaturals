# Owner PDF catalogue import

Source: local `Catalogue Ktnaturals.pdf`, a 21-page image-only catalogue. The original PDF is ignored by Git and Docker because a payment-instructions page is unrelated to this enquiry-only site. The small green KT Naturals mark in page 3 was cropped into `static/brand-logo.webp`; it is low resolution, so a proper source logo file would improve it. The footer tagline comes from pages 4 and 7.

## What was imported locally

- Page 2's price tables were visually checked and transcribed into `catalogue/catalogue_source.py`: 18 named products and 61 explicit INR pack-size prices. Dashes were not invented as variants. Category grouping into four site categories is editorial; product names and price rows retain the PDF wording and units.
- Founder history from pages 1 and 4 became the home introduction and published About page. The phone/WhatsApp number and Pan India delivery scope came from pages 3–4. Location, email, Instagram, opening hours, ingredients, storage, delivery/returns policy and privacy policy remain blank or unpublished because the PDF did not establish them.
- Selected non-medical process descriptions from product pages were used where clear. Claims about treating or preventing disease, immunity, infant suitability, certifications and payment instructions were not copied. Prices are presented as catalogue-listed and subject to owner confirmation.
- Product photographs were not available as clean standalone photographs. All 18 covers are explicitly labelled “CATALOGUE PLACEHOLDER / OWNER PHOTO PENDING”; replace them in the owner area with real photos before public launch. These are not the PDF posters, which contain mixed text and health claims.
- The six previous `is_demo=True` products, their unused demo categories and unreferenced demo image files were removed from the local database/media as requested. The restored and verified pre-import backup is retained at `data/catalogue-preimport-backups/snapshot-20261005T103942645670Z-b9a9a568`. A second stopped-writer snapshot of the new catalogue is at `data/catalogue-postimport-backups/snapshot-20261009T152855546741Z-977af340`; its isolated restore contained 18 products, 61 priced sizes and 18 media files. Two earlier snapshots, taken while a development server was still running, remain in the pre-import folder; **do not use those two as consistent backups**. They were not deleted after the terminal blocked that action.

## Review before using the listed prices publicly

- The PDF was produced in August 2025; current prices, stock, and delivery terms need owner confirmation. The site has not been publicly deployed.
- Table page 2 lists Khapli Wheat Flour at 5 kg ₹1,400 and 10 kg ₹2,400. Page 16 separately advertises ₹280/kg with a 5 kg minimum. The 10 kg table price is not equivalent to ₹280/kg; the importer preserves the table entry and flags the discrepancy rather than guessing a correction.
- The table lists ghee and honey in millilitres/litres, not grams. Those units are preserved exactly; confirm actual pack labels with the owner.
- Page 2's Flaxseed Oil 500 ml entry is ₹490 when checked visually; a raw OCR pass misread it. The stored value is ₹490.
- Published local listings are a preview with placeholder imagery. The WhatsApp handoff opens a prepared enquiry; it neither sends a message nor creates an order. Confirm the number, availability, final price, delivery charges and payment with the business.

## Reproduce safely

First back up both SQLite and media with all writers stopped. From a fresh database, `DJANGO_DEBUG=true .venv/bin/python manage.py import_catalogue --apply` creates **draft** records and never overwrites existing slugs or site settings. For a localhost-only preview, add `--publish-local`. Add `--replace-demo-local` only when explicitly replacing existing marked demo records; it deletes those records and unreferenced images but does not touch non-demo products. The `--refresh-placeholders-local` option regenerates only still-labelled importer placeholders, never owner-replaced photos. These local flags are refused when DEBUG is false or SITE_URL is not localhost/testserver.

Verification: `DJANGO_DEBUG=true .venv/bin/python qa/verify_catalogue_import.py` checks all 18 names, 61 prices, files, categories, story and demo removal against the transcribed source; `qa/check_seo.py` checks rendered sitemap/metadata. In production, import drafts, review every row and image, then publish via `/owner/`; do not copy the local development database into production.
