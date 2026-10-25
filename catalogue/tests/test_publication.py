from catalogue.tests.base import SiteTestCase
from django.core.exceptions import ValidationError
from django.apps import apps


class PublicationTest(SiteTestCase):
    def test_publish_requires_active_variant_and_cover(self):
        self.assertTrue(
            apps.get_app_config("catalogue").models.get("product"),
            "Product model must exist",
        )
        Product = apps.get_model("catalogue", "Product")
        p = Product.objects.create(name="Flour", slug="flour")
        p.status = "published"
        with self.assertRaises(ValidationError):
            p.save()
        self.assertEqual(Product.objects.get(pk=p.pk).status, "draft")
