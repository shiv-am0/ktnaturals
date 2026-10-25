"""Verify every imported PDF price row against the local catalogue database.
Run with DJANGO_DEBUG=true .venv/bin/python qa/verify_catalogue_import.py
"""

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import django
from django.conf import settings
from django.utils.text import slugify

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def main():
    django.setup()
    from catalogue.catalogue_source import ABOUT, ITEMS, WHATSAPP_DIGITS
    from catalogue.models import Category, Product, ProductVariant, SiteSettings

    assert Product.objects.filter(is_demo=True).count() == 0
    assert Product.objects.count() == len(ITEMS)
    assert Category.objects.count() == 4
    expected = {slugify(item.name): item for item in ITEMS}
    assert len(expected) == len(ITEMS)
    checked_variants = 0
    for product in Product.objects.select_related("category").prefetch_related(
        "variants", "images"
    ):
        source = expected.pop(product.slug)
        assert product.name == source.name
        assert product.category.name == source.category
        assert product.status == "published"
        assert not product.is_demo
        expected_prices = [(size, Decimal(price)) for size, price in source.prices]
        found_prices = [
            (variant.label, variant.price) for variant in product.variants.all()
        ]
        assert found_prices == expected_prices, (
            product.slug,
            found_prices,
            expected_prices,
        )
        assert product.images.count() == 1 and product.cover.image.storage.exists(
            product.cover.image.name
        )
        assert "placeholder" in product.cover.alt_text.lower()
        checked_variants += len(found_prices)
    assert not expected
    assert checked_variants == ProductVariant.objects.count()
    assert not list((Path(settings.MEDIA_ROOT) / "products").glob("demo-*.webp"))
    site = SiteSettings.load()
    assert site.whatsapp_number == WHATSAPP_DIGITS
    assert site.about == ABOUT and site.about_published
    assert not site.privacy_published and not site.delivery_returns_published
    report = {
        "catalogue_products": len(ITEMS),
        "priced_pack_sizes": checked_variants,
        "demo_products": 0,
        "categories": Category.objects.count(),
        "all_cover_placeholders_labelled": True,
        "story_published": True,
        "unapproved_policies_published": False,
    }
    path = Path("qa/evidence/catalogue-import.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
