# KT Naturals — Hermes build prompt (Phase 1)

Act as a product-minded full-stack engineer, UX designer, and practical SEO specialist. Build and verify a complete website for KT Naturals, a small brand selling products such as desi ghee, edible oils, and wheat flour. The purpose is to help customers discover products and contact the owner, reduce manual catalogue upkeep, and create a solid base for business growth. Work in the project repository and deliver a functioning application, not just a plan or static prototype.

Business today: The owner shares a PDF catalogue and handles enquiries, sales, invoices, delivery coordination, and Instagram manually through WhatsApp and other tools. There are approximately 15–20 products. In Phase 1, customers browse the site and start an enquiry on WhatsApp; the owner confirms the final order, payment, delivery charge, and availability there. Do not claim that a WhatsApp click creates an order or sends a message automatically.

1. Product scope

Public pages:
- Home: a clear brand introduction, featured products, category links, how to enquire, and visible calls to action.
- Products: a browseable catalogue with category filtering and simple search, attractive product cards, current prices, and clear availability.
- Product detail: multiple photos, description, pack sizes/variants with their own INR prices, optional ingredients and storage details when supplied, and a WhatsApp enquiry action for the chosen variant and quantity.
- About: owner-supplied brand story and production details.
- Contact: configured WhatsApp, phone, email, Instagram, location, opening hours, and delivery area where available.
- Delivery/returns and privacy information pages: editable by the owner; mark starter text as draft for review and never invent policies or legal claims.

Owner area:
- A separate, attractive, responsive dashboard under /owner/ with staff-only login. It must work on mobile as well as desktop.
- Manage product name, category, slug, short and full description, variants, prices, availability, featured status, images, image alt text, sort order, and publication status.
- Manage categories, homepage introduction, contact/WhatsApp details, Instagram link, and basic information pages.
- Clear draft, published, and archived states; previews accessible only to authenticated authorized staff.
- Simple actual counts such as published products and drafts. Do not display fake revenue, orders, or customer counts.
- Clear validation messages, confirmations before archive/removal, and no accidental data loss when editing.

Future possibilities include a proper order system, invoices, payments, delivery tools, and marketing workflows. Do not implement them now. Keep business logic separated enough to add them later.

2. Final technical choice

Use one Python/Django monolith: Django 5.2 LTS on a supported Python version, server-rendered Django templates, small amounts of vanilla JavaScript for the mobile menu and variant selection, and clean custom CSS with variables and responsive styles. A small build-time CSS tool is optional only if it genuinely saves work; no SPA, separate frontend API, HTMX dependency, or JavaScript server is needed for this catalogue.

Use SQLite for development AND the initial production deployment. It is free software, requires no managed database subscription, and fits a single-server site with 15–20 products and infrequent owner edits. Store the SQLite database on local persistent disk outside disposable containers. Do not place it on a network file system or ephemeral hosting disk. Keep Django models and migrations portable so a move to PostgreSQL is feasible if concurrent writes, more operational workflows, or multiple app servers later make that necessary. Do not add PostgreSQL, Redis, Kafka, Celery, microservices, or a paid database to this phase.

Use Django's built-in authentication, permissions, forms, CSRF protection, and sessions. Build a custom owner-facing interface; standard Django admin may remain as a restricted maintenance fallback but cannot be the only owner UI. Use Pillow for image validation and resizing.

Prepare Docker Compose with Django/Gunicorn and Caddy for a single Linux server, or a simpler equivalent if the existing repository has a good deployment setup. Host static files and uploaded media correctly and use HTTPS in production. The database engine has no license/subscription cost; the VPS/hosting, domain, optional external backup storage, and any paid email service are separate costs. Do not promise an entirely free production site.

3. Visual design

Create a clean, warm, trustworthy food brand. Suggested palette: ivory #FAF7F0, forest green #214B35, charcoal #26332B, sage #DDE8D8, and restrained ochre #B88746. Use generous white space, readable typography, authentic product photos when supplied, and subtle natural textures if they do not hurt load speed. Avoid flashy animation, fake discounts, countdowns, and generic stock imagery presented as the owner's actual products.

Mobile-first layout: accessible navigation, clear product photography, readable descriptions, touch-friendly buttons, and no horizontal overflow at 360px. Public CTA labels should say “Enquire on WhatsApp” or “Order via WhatsApp”; supporting copy must explain that the owner confirms the order. The admin should have readable forms, image previews, and usable mobile product lists.

4. Content and missing inputs

Brand name: KT Naturals. Currency: INR (₹). Language: English, with code/content structure allowing Hindi later if the owner requests it. Location, service area, WhatsApp number including country code, contact details, Instagram, logo, product photos, product sizes, prices, descriptions, and brand/policy copy must come from the owner.

If real data is unavailable, use visibly labelled demo content ONLY in the local development environment. Provide an explicit idempotent sample-data command for around six example products; do not automatically populate production or overwrite edited data. Do not fabricate a working phone number, reviews, certification, FSSAI number, health claims, sourcing methods, or the owner's story. Do not display “certified organic,” “A2,” “bilona,” “cold-pressed,” or similar attributes for individual products unless the owner supplies evidence/details. A brand-level description can follow owner-provided wording.

Configure the WhatsApp number through an owner setting or environment variable with validation. If missing, hide/disable enquiry buttons and show a helpful contact state. All pages should still render if products or optional settings are empty.

5. Data and catalogue behavior

Use models for Category, Product, ProductVariant, ProductImage, and SiteSettings. Categories need name, slug, display order, and active status. Products need stable unique slugs, text fields, category, draft/published/archived status, featured flag, and timestamps. Variants need a pack-size label (such as 500 g or 1 L), Decimal INR price, active/available flags, and order. Images need file, alt text, cover indicator, and order. Site settings hold owner-controlled brand/contact and page content.

A published product must have at least one valid active variant and a cover image. Price is nonnegative and never a float. Display a price range or “From ₹…” when variant prices differ. Drafts and archived products must not appear in public catalogue, related items, search results, sitemap, or structured data. Handle products and variants that are unavailable clearly. Archive instead of hard deleting products by default. Keep category deletion/reassignment safe and prevent duplicate slugs or multiple cover images.

Use SQLite-aware, short database transactions for updates. Do image processing outside long write transactions where possible. Avoid a long lock on the database while processing or uploading files. Design for one application server with mostly reads and occasional owner edits.

6. WhatsApp enquiry

Use an official click-to-chat link of the form https://wa.me/<international-number-digits-only>?text=<URL-encoded-message>. The selected variant and quantity should generate something like:

Hello KT Naturals! I would like to enquire about:
Product: <name>
Pack size: <variant>
Quantity: <positive integer>
Listed unit price: ₹<current server-side price>
Product link: <canonical URL>
Please confirm availability, delivery charges, and payment details.

Validate the number, variant belonging to the product, quantity, and availability. Never trust a client-submitted price. Encode text correctly, including ₹ and line breaks. If the data changed since the page loaded, present current information before redirecting. Use a normal link or server-generated redirect that works without JavaScript where feasible. There is no WhatsApp Business API, automated messaging, checkout, or Order record in this phase.

7. SEO and discovery: treat this as a core requirement

Implement crawlable, server-rendered HTML. Give each important page a descriptive unique title, meta description, clear H1, meaningful URL, and useful original copy. Make categories and product detail pages discoverable from navigation and internal links. Write good product descriptions using verified details rather than repeating generic keywords. Add appropriate breadcrumb navigation. Provide editable SEO title/description fields for products and categories with sensible generated defaults and length guidance.

Provide canonical URLs, a clean XML sitemap containing only public pages, robots.txt that does not block needed CSS/images, and noindex/access protection for /owner/ and private previews. Handle draft/archived product URLs sensibly (404 or gone where appropriate) and avoid indexed duplicate filter/search URLs. Add social sharing title, description, and real product image metadata when available. Put product image alt text and optimized image URLs in the HTML.

Add structured data only when it accurately matches the visible page and Google’s current eligibility rules: Organization/LocalBusiness if real business details are supplied, breadcrumbs where valid, and Product information when supported by the actual fields. Variant prices, currency, and availability must agree with the page. Do not invent ratings, reviews, shipping policies, discounts, or rich-result eligibility. Use Google’s official SEO and structured-data guidance and validate representative pages with appropriate tools.

Optimize images (including responsive sizes and WebP where practical), lazy-load below-the-fold media, avoid render-blocking scripts, and verify performance on mobile. Provide a launch guide for domain verification, submitting the sitemap in Google Search Console, and reviewing indexing and search queries after launch. Do not claim guaranteed rankings. Suggest a short, realistic content plan: one useful page for each actual product/category, genuine FAQs from customer questions, and owner-approved educational content. No mass-produced keyword pages.

8. Owner security and operational reliability

Require staff login and enforce authorization on every dashboard route and mutation; hidden UI controls alone do not count. No public registration or hardcoded password. Provide a documented secure command to create/reset the owner account. Support password change and POST-based logout. Apply appropriate session-cookie settings, CSRF protection, safe upload handling, escaping of owner-entered content, production DEBUG=False, allowed hosts, HTTPS/security headers, and login throttling using an appropriate maintained package or another reliable approach. Do not use arbitrary uploaded SVG or remote-image URL fetching.

Validate uploaded JPEG/PNG/WebP by content, set file-size and pixel limits, re-encode/resize, strip unnecessary metadata, randomize stored names, and show useful errors. Keep upload media persistent and protected from executable serving. Show responsive previews and alt text fields. Avoid logging credentials.

Create an actual backup/restore process for BOTH SQLite and uploaded images. Use SQLite’s supported backup mechanism for a consistent live database copy, not a naive file copy while it is in use. If using WAL mode, account for WAL/shm files and test the procedure. Include scheduled backups, retention, an owner-configured off-server destination, and a restore drill in a separate test location. Never present a persistent volume as sufficient backup by itself. Document how to move from SQLite to PostgreSQL later if growth warrants it.

9. Build, verify, and deliver

First inspect the repository and any AGENTS.md/instructions; preserve unrelated work. Write a concise plan, then implement in stages. Make reasonable implementation decisions yourself. Ask only for inputs that block a genuine next step; use labelled development placeholders for other missing inputs.

Run checks that demonstrate:
- Anonymous users cannot access owner pages or change data; CSRF works.
- The owner can log in, create a category/product, add images and two priced sizes, publish, edit, and archive, with changes persisting after restart.
- Public filters, product pages, size selection, and enquiry messages show the current correct data.
- Invalid images, price, quantity, or variant are safely rejected.
- Drafts/archives are absent from public pages and sitemap; generated metadata is accurate.
- Backup and restore recover database content and product images.
- Public and owner pages look good at roughly 360px, 768px, and 1440px, including keyboard operation and focus states.

Provide exact local run instructions, .env.example without secrets, migration commands, safe owner creation, production deployment and backup instructions, and a short OWNER_GUIDE.md. Include screenshots if browser tools are available. Report what actually passed and identify untested external steps. Do not deploy publicly, create paid services, or publish demo content without the real domain, brand details, product data, and owner authorization.

Success means a customer can find the right product in search or on the site and prepare an accurate WhatsApp enquiry, while the owner can maintain the catalogue easily from a phone without contacting a developer.
