"""Test browser requests as HTTPS, matching the Caddy-to-Django proxy contract."""

from django.test import Client, TestCase


class SecureClient(Client):
    def __init__(self, *args, **kwargs):
        # Caddy sets this header; a plain HTTP test request otherwise gets a
        # production-only 301 before it reaches the view under test.
        kwargs.setdefault("HTTP_X_FORWARDED_PROTO", "https")
        super().__init__(*args, **kwargs)


class SiteTestCase(TestCase):
    client_class = SecureClient
