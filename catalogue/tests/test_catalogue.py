from django.test import Client, override_settings
from catalogue.tests.base import SiteTestCase


class CatalogueTest(SiteTestCase):
    def test_empty_home_is_useful(self):
        response = self.client.get("/")
        self.assertContains(response, "KT Naturals")
        self.assertContains(response, "Browse products")

    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_http_redirects_to_https_and_proxy_requests_render(self):
        response = Client().get("/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "https://testserver/")
        self.assertEqual(self.client.get("/").status_code, 200)
