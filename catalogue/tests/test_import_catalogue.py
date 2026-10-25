import tempfile
from decimal import Decimal
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from catalogue.models import (
    Category,
    Product,
    ProductImage,
    ProductVariant,
    SiteSettings,
)
from catalogue.management.commands.import_catalogue import placeholder
from catalogue.tests.base import SiteTestCase


class CatalogueImportTest(SiteTestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name, DEBUG=True)
        self.override.enable()
        self.addCleanup(self.override.disable)

    def test_import_requires_explicit_action_and_production_cannot_publish(self):
        with self.assertRaises(CommandError):
            call_command("import_catalogue")
        with override_settings(DEBUG=False):
            with self.assertRaises(CommandError):
                call_command("import_catalogue", apply=True, publish_local=True)
        self.assertFalse(Product.objects.exists())

    def test_default_import_is_complete_draft_and_retries_preserve_owner_edits(self):
        call_command("import_catalogue", apply=True)
        self.assertEqual(Product.objects.count(), 18)
        self.assertEqual(ProductVariant.objects.count(), 61)
        self.assertEqual(Product.objects.filter(status="draft").count(), 18)
        self.assertEqual(Category.objects.count(), 4)
        self.assertTrue(all(p.cover for p in Product.objects.all()))
        self.assertTrue(
            all(
                "placeholder" in p.cover.alt_text.lower() for p in Product.objects.all()
            )
        )
        self.assertTrue(
            all(Path(p.cover.image.path).exists() for p in Product.objects.all())
        )
        self.assertEqual(
            ProductVariant.objects.get(
                product__name="CP Flaxseed Oil", label="500 ml"
            ).price,
            Decimal("490.00"),
        )
        self.assertEqual(
            ProductVariant.objects.get(
                product__name="Natural Forest Honey", label="1 L"
            ).price,
            Decimal("1700.00"),
        )
        site = SiteSettings.load()
        self.assertTrue(site.about_published)
        self.assertFalse(site.privacy_published)
        self.assertFalse(site.delivery_returns_published)
        self.assertEqual(site.whatsapp_number, "919329760025")
        item = Product.objects.get(name="CP Flaxseed Oil")
        item.description = "Owner-edited product detail"
        item.save()
        variant = item.variants.get(label="500 ml")
        variant.price = Decimal("491.00")
        variant.save()
        site.home_intro = "Owner-edited introduction"
        site.save()
        call_command("import_catalogue", apply=True)
        self.assertEqual(Product.objects.count(), 18)
        self.assertEqual(ProductVariant.objects.count(), 61)
        item.refresh_from_db()
        variant.refresh_from_db()
        self.assertEqual(item.description, "Owner-edited product detail")
        self.assertEqual(variant.price, Decimal("491.00"))
        self.assertEqual(SiteSettings.load().home_intro, "Owner-edited introduction")

    def test_explicit_local_preview_removes_only_demo_rows_and_media(self):
        old_category = Category.objects.create(name="Demo · Old", slug="demo-old")
        demo = Product.objects.create(
            name="Demo item", slug="demo-item", is_demo=True, category=old_category
        )
        demo.status = "published"
        # A published demo still needs a variant and cover to satisfy the model invariant.
        ProductVariant.objects.create(product=demo, label="1 kg", price=Decimal("1"))
        image = ProductImage(product=demo, alt_text="Demo", is_cover=True)
        image.image.save("demo.webp", ContentFile(b"old demo media"), save=True)
        old_path = Path(image.image.path)
        demo.save()
        with self.captureOnCommitCallbacks(execute=True):
            call_command(
                "import_catalogue",
                apply=True,
                publish_local=True,
                replace_demo_local=True,
            )
        self.assertFalse(Product.objects.filter(pk=demo.pk).exists())
        self.assertFalse(
            old_category.pk and Category.objects.filter(pk=old_category.pk).exists()
        )
        self.assertFalse(old_path.exists())
        self.assertEqual(
            Product.objects.filter(status="published", is_demo=False).count(), 18
        )
        self.assertEqual(Product.objects.count(), 18)

    def test_refresh_rewrites_only_unchanged_import_placeholders(self):
        call_command("import_catalogue", apply=True)
        product = Product.objects.get(name="CP Black Mustard Oil")
        photo = product.cover
        path = Path(photo.image.path)
        path.write_bytes(b"old small placeholder")
        call_command("import_catalogue", apply=True, refresh_placeholders_local=True)
        self.assertEqual(path.read_bytes(), placeholder(product.name).read())
        photo.alt_text = "Actual owner photo"
        photo.save()
        path.write_bytes(b"owner uploaded photo")
        call_command("import_catalogue", apply=True, refresh_placeholders_local=True)
        self.assertEqual(path.read_bytes(), b"owner uploaded photo")
