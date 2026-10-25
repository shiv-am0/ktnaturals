from catalogue.tests.base import SiteTestCase, SecureClient
from django.contrib.auth import get_user_model
from catalogue.models import Product, Category


class OwnerAccessTest(SiteTestCase):
    def test_repeated_failed_owner_logins_lock_out_even_correct_password(self):
        user = get_user_model().objects.create_user(
            "lockout_staff", password="test-only-not-real-password", is_staff=True
        )
        for attempt in range(5):
            self.client.post(
                "/owner/login/", {"username": user.username, "password": "incorrect"}
            )
        self.client.post(
            "/owner/login/",
            {"username": user.username, "password": "test-only-not-real-password"},
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_every_owner_route_requires_staff(self):
        routes = [
            "/owner/",
            "/owner/products/",
            "/owner/products/new/",
            "/owner/products/1/",
            "/owner/products/1/archive/",
            "/owner/products/1/preview/",
            "/owner/products/1/variants/new/",
            "/owner/products/1/variants/1/",
            "/owner/products/1/images/new/",
            "/owner/products/1/images/1/",
            "/owner/products/1/variants/1/remove/",
            "/owner/products/1/images/1/remove/",
            "/owner/categories/",
            "/owner/settings/",
            "/owner/password/",
        ]
        for route in routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 302, route)
            self.assertIn("/owner/login/", response.url)
            self.assertEqual(self.client.post(route, {}).status_code, 302, route)
        user = get_user_model().objects.create_user(
            "customer", password="test-only-not-real-password"
        )
        self.client.force_login(user)
        for route in routes:
            self.assertEqual(self.client.get(route).status_code, 403, route)
            self.assertEqual(self.client.post(route, {}).status_code, 403, route)

    def test_staff_can_create_draft_and_csrf_enforced(self):
        user = get_user_model().objects.create_user(
            "owner", password="test-only-not-real-password", is_staff=True
        )
        self.client.force_login(user)
        response = self.client.get("/owner/")
        self.assertContains(response, "Your pantry, at a glance")
        self.assertContains(self.client.get("/owner/products/new/"), "Save product")
        result = self.client.post(
            "/owner/products/new/",
            {"name": "Flour", "slug": "flour", "status": "draft", "sort_order": "0"},
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(Product.objects.get(slug="flour").status, "draft")
        csrf = SecureClient(enforce_csrf_checks=True)
        csrf.force_login(user)
        self.assertEqual(csrf.post("/owner/products/new/", {}).status_code, 403)
        self.assertEqual(self.client.get("/owner/logout/").status_code, 405)
        self.assertEqual(self.client.post("/owner/logout/").status_code, 302)
