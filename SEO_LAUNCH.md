# Search and launch checklist

## Before public launch

This is an enquiry catalogue, not online checkout. A WhatsApp link prepares a message; the customer must send it and the owner confirms availability, payment and delivery. No ranking, indexing, rich-result or merchant-listing eligibility is promised.

- Obtain owner approval for real product names, pack sizes, prices, availability, descriptions, image rights and alt text. Remove all development demo records from the production database; start production with an empty database rather than copying development.
- Supply the actual domain and canonical HTTPS SITE_URL, contact number including country code, contact details and approved brand story. Supply location/delivery details only if verified. Review and approve delivery/returns and privacy copy before removing its draft status.
- Select one canonical hostname; redirect other domain variants at the reverse proxy. Confirm all sitemap URLs and social image URLs use the canonical HTTPS host.
- Test the public home, catalogue, every category and product with JavaScript disabled. Confirm useful titles, descriptions, one clear H1, breadcrumbs and image alt text. Product and category SEO fields should describe the actual content, not promise unsupported health benefits or certifications.
- Confirm drafts/archives and staff previews cannot be accessed anonymously or found in sitemap, navigation, search or related products. Search/filter URLs should not become indexed duplicate pages. Keep CSS and images crawlable.
- Inspect server-rendered JSON-LD. Product price strings, INR currency, variant labels and availability must agree with visible content. Do not add invented ratings/reviews, returns, shipping or organization location. Google explicitly says not to use AggregateOffer for a set of product variants. Do not equate passing a JSON parser with passing Google's eligibility checks.

## Domain and Google verification (owner-authorized external steps)

1. Deploy only after the owner's explicit approval, with production DEBUG disabled, HTTPS working, no demo content, correct persistent storage and a successful backup restore drill.
2. Open https://search.google.com/search-console and add a Domain property for the real domain. Add Google's provided DNS TXT record at the domain provider, then verify. Keep the verification record.
3. Submit `https://YOUR-REAL-DOMAIN/sitemap.xml` in Search Console's Sitemaps section. Inspect a representative category and product with URL Inspection, including the live test. Check that Google can fetch rendered content and images.
4. At https://search.google.com/test/rich-results test a representative real product. Use the code input for local HTML if needed, but the URL test on production remains necessary. Also inspect https://validator.schema.org/ for schema syntax. Resolve errors; optional warnings are not a reason to invent missing facts.
5. Run mobile Lighthouse/PageSpeed against production, record actual results, and inspect LCP, CLS and INP in field data when enough traffic exists. Local browser timings are diagnostic only, not a production performance promise.
6. Review indexing, sitemap status and product enhancement reports after launch. Review search queries and relevant landing pages after several weeks. Fix genuine content gaps and broken links; requesting indexing does not guarantee inclusion.

## Realistic content plan

- One useful page per actual product: what it is, verified ingredients when supplied, available pack sizes, current prices and owner-approved storage instructions.
- One page per actual category with a short original introduction and links to its products.
- Collect recurring customer questions from genuine WhatsApp enquiries; publish owner-approved answers about selection, storage and the enquiry process.
- Add educational content only where the owner can verify it. Do not mass-produce keyword pages, fake reviews, health claims or service-area pages for places not actually served.

## Official guidance consulted

- SEO starter guide: https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- Product markup overview (product snippets versus merchant listings): https://developers.google.com/search/docs/appearance/structured-data/product
- Product snippet requirements, offer pricing and variant restrictions: https://developers.google.com/search/docs/appearance/structured-data/product-snippet
- Variant markup: https://developers.google.com/search/docs/appearance/structured-data/product-variants
- Sitemap construction/submission: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap

Public deployment, DNS verification, Search Console submission, live Google rich-results validation and production field performance cannot be verified without the real domain, content and owner authorization. They remain launch tasks, not completed checks.
