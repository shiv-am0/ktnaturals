import json
import re
from catalogue.tests.base import SiteTestCase
from django.contrib.auth import get_user_model
from catalogue.tests.test_public import product
from catalogue.models import SiteSettings


class SEOTest(SiteTestCase):
    def test_metadata_sitemap_structured_data_and_private_noindex(self):
        p = product()
        product("Hidden", "hidden", "draft")
        product("Old", "old", "archived")
        page = self.client.get(p.get_absolute_url())
        self.assertContains(page, 'rel="canonical"')
        self.assertContains(page, 'property="og:image"')
        blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>',
            page.content.decode(),
            re.S,
        )
        self.assertTrue(blocks)
        data = json.loads(blocks[0])
        node = next(n for n in data["@graph"] if n["@type"] == "Product")
        self.assertEqual([o["price"] for o in node["offers"]], ["90.00", "170.00"])
        self.assertEqual(node["offers"][0]["priceCurrency"], "INR")
        sitemap = self.client.get("/sitemap.xml")
        self.assertContains(sitemap, "/products/wheat-flour/")
        self.assertNotContains(sitemap, "/products/hidden/")
        self.assertNotContains(sitemap, "/products/old/")
        self.assertContains(self.client.get("/robots.txt"), "Disallow: /owner/")
        self.assertContains(self.client.get("/products/?q=flour"), "noindex, follow")
        self.assertEqual(
            self.client.get("/owner/login/")["X-Robots-Tag"], "noindex, nofollow"
        )

    def test_json_script_injection_and_unreviewed_pages_not_public(self):
        p = product(name="Flour </script><script>alert(1)</script>")
        page = self.client.get(p.get_absolute_url()).content.decode()
        self.assertNotIn("</script><script>alert(1)", page)
        site = SiteSettings.objects.create(
            about="Private story", privacy="UNREVIEWED POLICY"
        )
        self.assertNotContains(self.client.get("/about/"), "Private story")
        self.assertNotContains(self.client.get("/privacy/"), "UNREVIEWED POLICY")
        for url in ["/about/", "/contact/", "/delivery-returns/", "/privacy/"]:
            self.assertEqual(self.client.get(url).status_code, 200)
        site.about_published = True
        site.save()
        self.assertContains(self.client.get("/about/"), "Private story")
