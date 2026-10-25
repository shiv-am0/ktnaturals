from catalogue.tests.base import SiteTestCase
from catalogue.tests.test_public import product
from catalogue.models import SiteSettings
from urllib.parse import urlparse, parse_qs


class EnquiryTest(SiteTestCase):
    def setUp(self):
        self.p = product()
        SiteSettings.objects.create(whatsapp_number="919876543210")

    def test_server_price_variant_quantity_and_stale_confirmation(self):
        page = self.client.get(self.p.get_absolute_url())
        self.assertIn(
            "quote", page.context, "Detail must provide a signed server quote"
        )
        quote = page.context["quote"]
        v = self.p.variants.first()
        payload = {"variant": v.pk, "quantity": "2", "quote": quote, "price": "0.01"}
        response = self.client.post("/products/wheat-flour/enquire/", payload)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("https://wa.me/919876543210?text="))
        text = parse_qs(urlparse(response.url).query)["text"][0]
        self.assertIn("Quantity: 2", text)
        self.assertIn("Listed unit price: ₹90.00", text)
        self.assertIn("Pack size: 500 g", text)
        v.price = "99.00"
        v.save()
        stale = self.client.post("/products/wheat-flour/enquire/", payload)
        self.assertEqual(stale.status_code, 200)
        self.assertContains(stale, "Details have changed")
        self.assertContains(stale, "99.00")
        payload["quote"] = stale.context["quote"]
        self.assertEqual(
            self.client.post("/products/wheat-flour/enquire/", payload).status_code, 302
        )

    def test_rejects_invalid_unavailable_and_missing_contact(self):
        v = self.p.variants.first()
        quote = self.client.get(self.p.get_absolute_url()).context.get("quote", "")
        url = "/products/wheat-flour/enquire/"
        for quantity in ["0", "-1", "1.5", "abc", "100", "999999999999"]:
            self.assertEqual(
                self.client.post(
                    url, {"variant": v.pk, "quantity": quantity, "quote": quote}
                ).status_code,
                400,
            )
        other = product("Other", "other").variants.first()
        self.assertEqual(
            self.client.post(
                url, {"variant": other.pk, "quantity": "1", "quote": quote}
            ).status_code,
            400,
        )
        v.available = False
        v.save()
        self.assertEqual(
            self.client.post(
                url, {"variant": v.pk, "quantity": "1", "quote": quote}
            ).status_code,
            400,
        )
        SiteSettings.objects.update(whatsapp_number="")
        self.assertEqual(
            self.client.post(
                url, {"variant": v.pk, "quantity": "1", "quote": quote}
            ).status_code,
            400,
        )
