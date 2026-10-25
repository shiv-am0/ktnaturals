from django.test import override_settings
from catalogue.tests.base import SiteTestCase
from django.core.management import call_command, get_commands
from django.core.management.base import CommandError
from catalogue.models import Product, SiteSettings
import tempfile


class DemoTest(SiteTestCase):
    def test_explicit_debug_only_six_demo_products_idempotent(self):
        self.assertIn("seed_demo", get_commands())
        with override_settings(DEBUG=False):
            with self.assertRaises(CommandError):
                call_command("seed_demo", confirm_local=True)
        with (
            tempfile.TemporaryDirectory() as media,
            override_settings(DEBUG=True, MEDIA_ROOT=media),
        ):
            with self.assertRaises(CommandError):
                call_command("seed_demo")
            call_command("seed_demo", confirm_local=True)
            self.assertEqual(Product.objects.filter(is_demo=True).count(), 6)
            self.assertEqual(Product.objects.filter(status="published").count(), 6)
            self.assertTrue(all(p.cover and p.available for p in Product.objects.all()))
            p = Product.objects.first()
            p.name = "Owner edited demo"
            p.save()
            call_command("seed_demo", confirm_local=True)
            self.assertEqual(Product.objects.count(), 6)
            p.refresh_from_db()
            self.assertEqual(p.name, "Owner edited demo")
            self.assertEqual(SiteSettings.load().whatsapp_number, "")
