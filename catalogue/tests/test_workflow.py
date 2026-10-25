import io
import tempfile
from pathlib import Path
from PIL import Image
from django.test import override_settings
from catalogue.tests.base import SiteTestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from catalogue.models import Product, ProductImage, ProductVariant


def upload(name="photo.png"):
    data = io.BytesIO()
    Image.new("RGB", (1800, 1200), "#d8dfb0").save(data, "PNG")
    return SimpleUploadedFile(name, data.getvalue(), content_type="image/png")


class WorkflowTest(SiteTestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.user = get_user_model().objects.create_user("owner", is_staff=True)
        self.client.force_login(self.user)
        self.p = Product.objects.create(name="Flour", slug="flour")

    def test_owner_adds_two_sizes_safe_photo_publishes_and_archives(self):
        for label, price in [("500 g", "90.00"), ("1 kg", "170.00")]:
            response = self.client.post(
                f"/owner/products/{self.p.pk}/variants/new/",
                {
                    "label": label,
                    "price": price,
                    "active": "on",
                    "available": "on",
                    "sort_order": "0",
                },
            )
            self.assertEqual(response.status_code, 302)
        self.assertEqual(self.p.variants.count(), 2)
        result = self.client.post(
            f"/owner/products/{self.p.pk}/images/new/",
            {
                "image": upload(),
                "alt_text": "Flour in a jar",
                "is_cover": "on",
                "sort_order": "0",
            },
        )
        self.assertEqual(result.status_code, 302)
        photo = self.p.images.get()
        self.assertTrue(photo.image.name.endswith(".webp"))
        self.assertNotIn("photo", photo.image.name)
        with Image.open(photo.image.path) as image:
            self.assertLessEqual(max(image.size), 1600)
            self.assertEqual(image.format, "WEBP")
        edit = self.client.get(f"/owner/products/{self.p.pk}/")
        response = self.client.post(
            f"/owner/products/{self.p.pk}/",
            {
                "name": "Flour",
                "slug": "flour",
                "status": "published",
                "sort_order": "0",
                "revision": edit.context["form"]["revision"].value(),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.p.refresh_from_db()
        self.assertEqual(self.p.status, "published")
        self.assertEqual(self.client.get("/products/flour/").status_code, 200)
        confirmation = self.client.get(f"/owner/products/{self.p.pk}/archive/")
        self.assertEqual(confirmation.status_code, 200)
        self.client.post(
            f"/owner/products/{self.p.pk}/archive/",
            {"revision": confirmation.context["revision"]},
        )
        self.p.refresh_from_db()
        self.assertEqual(self.p.status, "archived")
        self.assertEqual(self.client.get("/products/flour/").status_code, 404)

    def test_bad_uploads_negative_prices_and_last_cover_removal_rejected(self):
        url = f"/owner/products/{self.p.pk}/images/new/"
        for bad in [
            SimpleUploadedFile(
                "evil.svg", b'<svg onload="alert(1)"/>', content_type="image/svg+xml"
            ),
            SimpleUploadedFile("bad.png", b"not an image", content_type="image/png"),
        ]:
            self.assertEqual(
                self.client.post(
                    url, {"image": bad, "alt_text": "bad", "sort_order": "0"}
                ).status_code,
                200,
            )
        self.assertEqual(self.p.images.count(), 0)
        result = self.client.post(
            f"/owner/products/{self.p.pk}/variants/new/",
            {"label": "1 kg", "price": "-1", "sort_order": "0", "active": "on"},
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.p.variants.count(), 0)

    def test_removing_photo_removes_public_file_after_commit(self):
        self.client.post(
            f"/owner/products/{self.p.pk}/images/new/",
            {
                "image": upload(),
                "alt_text": "Temporary photo",
                "is_cover": "on",
                "sort_order": "0",
            },
        )
        photo = self.p.images.get()
        old_path = Path(photo.image.path)
        self.assertTrue(old_path.exists())
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                f"/owner/products/{self.p.pk}/images/{photo.pk}/remove/"
            )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(old_path.exists())

    def test_replacing_photo_removes_old_public_file_after_commit(self):
        self.client.post(
            f"/owner/products/{self.p.pk}/images/new/",
            {
                "image": upload(),
                "alt_text": "Original photo",
                "is_cover": "on",
                "sort_order": "0",
            },
        )
        photo = self.p.images.get()
        old_path = Path(photo.image.path)
        revision = self.client.get(
            f"/owner/products/{self.p.pk}/images/{photo.pk}/"
        ).context["revision"]
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                f"/owner/products/{self.p.pk}/images/{photo.pk}/",
                {
                    "image": upload("replacement.png"),
                    "alt_text": "Replacement photo",
                    "is_cover": "on",
                    "sort_order": "0",
                    "revision": revision,
                },
            )
        self.assertEqual(response.status_code, 302)
        photo.refresh_from_db()
        self.assertTrue(Path(photo.image.path).exists())
        self.assertFalse(old_path.exists())
