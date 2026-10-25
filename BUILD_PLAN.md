# KT Naturals Phase 1 build

## Scope
One Django 5.2 monolith, SQLite on local persistent storage, server-rendered templates, custom responsive owner area, and WhatsApp enquiry preparation. No checkout/order/payment system or public deployment. Source requirements: KT_Naturals_Hermes_Build_Prompt.md.

## Implementation stages
1. Models and publish invariants; safe images and variants; public catalogue and owner editing with vertical regression tests.
2. SEO metadata/discovery, enquiry server validation, authentication and throttling, content settings and explicit local demo data.
3. Docker/Gunicorn/Caddy deployment, consistent SQLite/media backup and safe restore, operations and owner documentation.
4. Independent regression execution, local browser checks at 360/768/1440 pixels, representative metadata inspection, restore drill and production configuration checks.

## Verification evidence to collect
- Staff-only owner routes/mutations, anonymous and non-staff denial, CSRF, POST logout, password change and throttling.
- Category/product/variant/image lifecycle and publication requirements, valid and invalid uploads, negative price rejection, safe archive and persistent edits.
- Search/category filters, variant selection, unavailable stock, correct URL-encoded WhatsApp text and stale-price confirmation, missing-contact behavior.
- Draft/archive isolation, noindex staff and duplicate URLs, canonical metadata, sitemap and server-rendered JSON-LD price consistency.
- Consistent SQLite snapshot and uploaded-file restore into a separate directory with checksums and corruption/path validation.
- Browser screenshots, no horizontal overflow, working keyboard navigation, public rendering without JavaScript, owner forms and mobile menus.
- Real production configuration/container checks where local Docker/network allow; no implied verification of DNS, TLS issuance or off-server backup delivery.

## Missing owner inputs
Domain, deployment authorization, genuine logo/photos, products/pack sizes/prices/descriptions, contact details, story and approved policies. These do not block local development. No working contact number or unsupported business claims will be invented.

## Evidence/report
Actual completed checks and remaining launch prerequisites are recorded in VERIFICATION.md after execution, with screenshots under qa/evidence/. SEO_LAUNCH.md explains owner-authorized search setup. No git repository existed at the start; original prompt is preserved.
