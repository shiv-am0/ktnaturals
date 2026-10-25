from catalogue.tests.base import SiteTestCase
from catalogue.tests.test_public import product


class DesignTest(SiteTestCase):
    def test_home_has_featured_products_categories_and_how_to_enquire(self):
        p = product()
        p.featured = True
        p.save()
        response = self.client.get("/")
        self.assertContains(response, "Wheat flour")
        self.assertContains(response, "How to enquire")
        self.assertContains(response, 'aria-controls="public-nav"')
        self.assertContains(response, "Delivery &amp; returns")
        self.assertContains(response, '/static/brand-logo.webp', count=2)
