from catalogue.tests.base import SiteTestCase
from catalogue.models import (
    Category,
    Product,
    ProductVariant,
    ProductImage,
    SiteSettings,
)
from decimal import Decimal


def product(name="Wheat flour", slug="wheat-flour", status="published", category=None):
    p = Product.objects.create(
        name=name,
        slug=slug,
        category=category,
        short_description="Everyday kitchen essentials.",
    )
    ProductVariant.objects.create(product=p, label="500 g", price=Decimal("90.00"))
    ProductVariant.objects.create(product=p, label="1 kg", price=Decimal("170.00"))
    ProductImage.objects.create(
        product=p, image="products/test.webp", alt_text=name, is_cover=True
    )
    p.status = status
    p.save()
    return p


class PublicTest(SiteTestCase):
    def test_category_without_editorial_copy_still_has_description(self):
        Category.objects.create(name="Flours", slug="flours")
        response = self.client.get("/categories/flours/")
        self.assertContains(response, "Browse Flours products at KT Naturals")
        self.assertContains(
            response,
            'name="description" content="Browse Flours products at KT Naturals',
        )
        self.assertContains(response, "<title>Flours products | KT Naturals</title>")

    def test_custom_product_seo_title_is_rendered_in_document_title(self):
        item = product()
        item.seo_title = "Fresh wheat flour sizes | KT Naturals"
        item.save()
        self.assertContains(
            self.client.get(item.get_absolute_url()),
            "<title>Fresh wheat flour sizes | KT Naturals</title>",
        )

    def test_product_jsonld_escapes_script_termination(self):
        item = product(name="Unsafe </script><script>alert(1)</script>")
        page = self.client.get(item.get_absolute_url()).content.decode()
        self.assertNotIn('"name": "Unsafe </script>', page)
        self.assertIn('"name": "Unsafe \\u003c/script\\u003e', page)

    def test_unapproved_information_pages_are_not_indexed(self):
        for path in ("/about/", "/delivery-returns/", "/privacy/"):
            response = self.client.get(path)
            self.assertContains(response, 'name="robots" content="noindex')
            self.assertNotIn(path, self.client.get("/sitemap.xml").content.decode())
        site = SiteSettings.objects.create(
            privacy="Owner approved copy", privacy_published=True
        )
        self.assertNotContains(
            self.client.get("/privacy/"), 'name="robots" content="noindex'
        )
        self.assertIn("/privacy/", self.client.get("/sitemap.xml").content.decode())

    def test_card_starting_price_uses_available_sizes(self):
        item = product()
        cheap, available = list(item.variants.all())
        cheap.available = False
        cheap.save()
        self.assertEqual(item.price_display, "₹170.00")
        self.assertContains(self.client.get("/products/"), "₹170.00")

    def test_catalogue_filters_and_detail_isolate_drafts(self):
        c = Category.objects.create(name="Flours", slug="flours")
        p = product(category=c)
        draft = product("Secret draft", "secret", status="draft")
        product("Archived oil", "archived", status="archived")
        response = self.client.get("/products/")
        self.assertContains(response, "Wheat flour")
        self.assertContains(response, "From ₹90.00")
        self.assertNotContains(response, "Secret draft")
        self.assertNotContains(response, "Archived oil")
        self.assertNotContains(self.client.get("/products/?q=oil"), "Wheat flour")
        self.assertContains(self.client.get("/categories/flours/"), "Wheat flour")
        self.assertEqual(self.client.get("/products/secret/").status_code, 404)
        detail = self.client.get("/products/wheat-flour/")
        self.assertContains(detail, "500 g")
        self.assertContains(detail, "170.00")
        self.assertContains(detail, "Enquiries are not available yet")
