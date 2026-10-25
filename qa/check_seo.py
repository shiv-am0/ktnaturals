"""Validate local rendered SEO against persisted catalogue data, without publishing."""

import json
import os
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from django.conf import settings
from django.test import Client
from catalogue.models import Product


class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.canonical = ""
        self.h1_count = 0
        self.schemas = []
        self.in_title = False
        self.in_schema = False
        self.buffer = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.h1_count += 1
        if tag == "meta" and attrs.get("name") == "description":
            self.description = attrs.get("content", "")
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href", "")
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.in_schema = True
            self.buffer = ""

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_schema:
            self.buffer += data

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "script" and self.in_schema:
            self.schemas.append(json.loads(self.buffer))
            self.in_schema = False


def main():
    client = Client(HTTP_HOST=urlsplit(settings.SITE_URL).netloc)
    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200, sitemap.status_code
    urls = [
        node.text
        for node in ET.fromstring(sitemap.content).iter()
        if node.tag.endswith("}loc")
    ]
    assert urls, "Empty sitemap"
    results = []
    titles = set()
    products = {
        p.get_absolute_url(): p for p in Product.objects.filter(status="published")
    }
    for url in urls:
        path = urlsplit(url).path
        response = client.get(path)
        assert response.status_code == 200, (path, response.status_code)
        head = HeadParser()
        head.feed(response.content.decode())
        assert head.title and head.title not in titles, (
            path,
            "Missing/duplicate title",
            head.title,
        )
        assert head.description, (path, "No meta description")
        assert head.h1_count == 1, (path, "H1 count", head.h1_count)
        assert head.canonical == url, (path, "Canonical mismatch", head.canonical, url)
        titles.add(head.title)
        flat = []
        for schema in head.schemas:
            flat.extend(
                schema if isinstance(schema, list) else schema.get("@graph", [schema])
            )
        product_schema = [s for s in flat if s.get("@type") == "Product"]
        if path in products:
            assert len(product_schema) == 1, (
                path,
                "Missing or duplicate Product schema",
            )
            expected = sorted(
                str(v.price) for v in products[path].variants.filter(active=True)
            )
            for schema in product_schema:
                offers = schema.get("offers", [])
                offers = offers if isinstance(offers, list) else [offers]
                assert all(
                    o.get("@type") == "Offer" and o.get("priceCurrency") == "INR"
                    for o in offers
                ), (path, offers)
                assert sorted(str(o["price"]) for o in offers) == expected, (
                    path,
                    expected,
                    offers,
                )
                assert not schema.get("aggregateRating") and not schema.get("review"), (
                    path
                )
        results.append(
            {
                "path": path,
                "title": head.title,
                "canonical": head.canonical,
                "schemas": [s.get("@type") for s in flat],
            }
        )
    for product in Product.objects.exclude(status="published"):
        assert product.get_absolute_url() not in [urlsplit(u).path for u in urls]
        assert client.get(product.get_absolute_url()).status_code == 404
    target = Path("qa/evidence/seo.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(results, indent=2))
    print(
        f"Validated {len(results)} sitemap pages: unique titles, descriptions, one H1, canonical URLs, JSON-LD parsing and present offer prices. Draft/archive URLs excluded."
    )
    print(
        "This is local consistency validation, not Google rich-result eligibility validation."
    )


if __name__ == "__main__":
    main()
