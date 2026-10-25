from catalogue.tests.base import SiteTestCase
from django.contrib.auth import get_user_model
from catalogue.tests.test_public import product
from catalogue.models import Category, Product, SiteSettings


class IntegrityTest(SiteTestCase):
    def setUp(self):
        self.client.force_login(
            get_user_model().objects.create_user("owner", is_staff=True)
        )
        self.p = product()

    def test_stale_product_edits_do_not_overwrite_newer_changes(self):
        url = f"/owner/products/{self.p.pk}/"
        token = self.client.get(url).context["form"]["revision"].value()
        self.p.name = "Newer owner edit"
        self.p.save()
        response = self.client.post(
            url,
            {
                "name": "Old page edit",
                "slug": self.p.slug,
                "status": "published",
                "sort_order": "0",
                "revision": token,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "changed since you opened")
        self.p.refresh_from_db()
        self.assertEqual(self.p.name, "Newer owner edit")

    def test_last_active_variant_and_cover_cannot_be_removed(self):
        self.p.variants.last().delete()
        v = self.p.variants.first()
        i = self.p.images.first()
        revision = self.client.get(
            f"/owner/products/{self.p.pk}/variants/{v.pk}/"
        ).context["revision"]
        response = self.client.post(
            f"/owner/products/{self.p.pk}/variants/{v.pk}/",
            {
                "label": v.label,
                "price": "90.00",
                "sort_order": "0",
                "revision": revision,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "To publish")
        v.refresh_from_db()
        self.assertTrue(v.active)
        response = self.client.post(
            f"/owner/products/{self.p.pk}/images/{i.pk}/remove/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.p.images.filter(pk=i.pk).exists())

    def test_stale_variant_edit_does_not_replace_newer_price(self):
        variant = self.p.variants.first()
        url = f"/owner/products/{self.p.pk}/variants/{variant.pk}/"
        token = self.client.get(url).context["revision"]
        variant.price = "125.00"
        variant.save()
        self.p.save()
        response = self.client.post(
            url,
            {
                "label": variant.label,
                "price": "90.00",
                "sort_order": "0",
                "active": "on",
                "available": "on",
                "revision": token,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "changed since you opened")
        variant.refresh_from_db()
        self.assertEqual(str(variant.price), "125.00")

    def test_stale_archive_confirmation_does_not_hide_newer_product(self):
        url = f"/owner/products/{self.p.pk}/archive/"
        token = self.client.get(url).context["revision"]
        self.p.short_description = "A newer edit"
        self.p.save()
        response = self.client.post(url, {"revision": token})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "changed since you opened")
        self.p.refresh_from_db()
        self.assertEqual(self.p.status, "published")

    def test_stale_category_edit_does_not_replace_newer_copy(self):
        category = Category.objects.create(name="Flours", slug="flours")
        url = f"/owner/categories/?edit={category.pk}"
        token = self.client.get(url).context["revision"]
        category.description = "Newer category introduction"
        category.save()
        response = self.client.post(
            url,
            {
                "name": "Flours",
                "slug": "flours",
                "description": "Old introduction",
                "display_order": "0",
                "active": "on",
                "revision": token,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "changed since you opened")
        category.refresh_from_db()
        self.assertEqual(category.description, "Newer category introduction")

    def test_stale_site_settings_edit_does_not_replace_newer_copy(self):
        site = SiteSettings.objects.create(home_intro="New homepage")
        token = self.client.get("/owner/settings/").context["revision"]
        site.home_intro = "Newer homepage edit"
        site.save()
        response = self.client.post(
            "/owner/settings/",
            {
                "brand_name": "KT Naturals",
                "home_intro": "Old homepage",
                "revision": token,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "changed since you opened")
        site.refresh_from_db()
        self.assertEqual(site.home_intro, "Newer homepage edit")
