"""Local owner-browser lifecycle; uses disposable staff and catalogue records.
Run with DJANGO_DEBUG=true uv run --with playwright --python .venv/bin/python python qa/owner_flow.py
"""

import io
import os
import secrets
import sys
import uuid
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
# This disposable single-thread browser harness reads/writes local test rows
# while Playwright's synchronous facade owns an event loop in this thread.
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import django

django.setup()
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from catalogue.models import Category, Product
from PIL import Image
from playwright.sync_api import sync_playwright


def main():
    tag = uuid.uuid4().hex[:10]
    username = "qa_" + tag
    password = secrets.token_urlsafe(32)
    user = get_user_model().objects.create_user(
        username, password=password, is_staff=True
    )
    category_slug = "qa-" + tag
    product_slug = "qa-product-" + tag
    path = Path("qa/evidence/owner")
    path.mkdir(parents=True, exist_ok=True)
    browser = None
    images = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path="/usr/bin/chromium",
                headless=True,
                args=["--no-sandbox"],
            )
            page = browser.new_page(
                viewport={"width": 360, "height": 800}, reduced_motion="reduce"
            )
            page.goto("http://127.0.0.1:8000/owner/")
            assert "/owner/login/" in page.url
            page.locator("#id_username").fill(username)
            page.locator("#id_password").fill(password)
            page.locator('button:has-text("Sign in")').click()
            assert page.url.rstrip("/") == "http://127.0.0.1:8000/owner"
            page.screenshot(path=str(path / "dashboard-360.png"), full_page=True)
            page.add_script_tag(path="/tmp/ktnaturals-axe.min.js")
            violations = page.evaluate(
                "async () => (await axe.run(document, {runOnly:{type:'tag', values:['wcag2a','wcag2aa','wcag21aa']}})).violations"
            )
            assert not violations, [(v["id"], len(v["nodes"])) for v in violations]
            page.goto("http://127.0.0.1:8000/owner/categories/")
            page.locator("#id_name").fill("QA category " + tag)
            page.locator("#id_slug").fill(category_slug)
            page.locator('button:has-text("Save category")').click()
            assert Category.objects.filter(slug=category_slug).exists()
            category = Category.objects.get(slug=category_slug)
            page.goto("http://127.0.0.1:8000/owner/products/new/")
            page.locator("#id_name").fill("QA product " + tag)
            page.locator("#id_slug").fill(product_slug)
            page.locator("#id_category").select_option(str(category.pk))
            page.locator("#id_short_description").fill("Disposable browser test entry.")
            page.locator('button:has-text("Save product")').click()
            item = Product.objects.get(slug=product_slug)
            assert item.status == "draft"
            for label, price in [("500 g", "90.00"), ("1 kg", "170.00")]:
                page.goto(
                    f"http://127.0.0.1:8000/owner/products/{item.pk}/variants/new/"
                )
                page.locator("#id_label").fill(label)
                page.locator("#id_price").fill(price)
                page.locator('button:has-text("Save pack size")').click()
                assert item.variants.filter(label=label).exists()
            page.goto(f"http://127.0.0.1:8000/owner/products/{item.pk}/images/new/")
            picture = io.BytesIO()
            Image.new("RGB", (1200, 1200), "#a3b081").save(picture, "PNG")
            page.locator("#id_image").set_input_files(
                {
                    "name": "qa-photo.png",
                    "mimeType": "image/png",
                    "buffer": picture.getvalue(),
                }
            )
            page.locator("#id_alt_text").fill(
                "Disposable product image for browser testing"
            )
            page.locator("#id_is_cover").check()
            page.locator('button:has-text("Save photo")').click()
            item.refresh_from_db()
            assert item.images.filter(is_cover=True).exists()
            images = [image.image.name for image in item.images.all()]
            page.goto(f"http://127.0.0.1:8000/owner/products/{item.pk}/")
            page.locator("#id_status").select_option("published")
            page.locator('button:has-text("Save product")').click()
            item.refresh_from_db()
            assert item.status == "published", page.locator("body").inner_text()[:1000]
            page.goto("http://127.0.0.1:8000/products/" + product_slug + "/")
            assert (
                "500 g" in page.locator("body").inner_text()
                and "170.00" in page.locator("body").inner_text()
            )
            variant = item.variants.get(label="500 g")
            page.goto(
                f"http://127.0.0.1:8000/owner/products/{item.pk}/variants/{variant.pk}/"
            )
            page.locator("#id_price").fill("95.00")
            page.locator('button:has-text("Save pack size")').click()
            variant.refresh_from_db()
            assert str(variant.price) == "95.00"
            page.goto(f"http://127.0.0.1:8000/owner/products/{item.pk}/")
            page.locator("#id_short_description").fill("Updated in the owner browser.")
            page.locator('button:has-text("Save product")').click()
            page.goto("http://127.0.0.1:8000/products/" + product_slug + "/")
            assert "Updated in the owner browser." in page.locator("body").inner_text()
            assert "95.00" in page.locator("body").inner_text()
            for width in (360, 768, 1440):
                page.set_viewport_size({"width": width, "height": 900})
                page.goto(f"http://127.0.0.1:8000/owner/products/{item.pk}/")
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth"
                ), width
                page.screenshot(path=str(path / f"editor-{width}.png"), full_page=True)
                page.add_script_tag(path="/tmp/ktnaturals-axe.min.js")
                violations = page.evaluate(
                    "async () => (await axe.run(document, {runOnly:{type:'tag', values:['wcag2a','wcag2aa','wcag21aa']}})).violations"
                )
                assert not violations, (
                    width,
                    [(v["id"], len(v["nodes"])) for v in violations],
                )
            page.goto(f"http://127.0.0.1:8000/owner/products/{item.pk}/archive/")
            page.locator('button:has-text("Archive")').click()
            item.refresh_from_db()
            assert item.status == "archived"
            assert (
                page.request.get(
                    "http://127.0.0.1:8000/products/" + product_slug + "/"
                ).status
                == 404
            )
            print(
                "Browser owner lifecycle passed: staff login, category, draft, two priced sizes, photo, publish, edit product/price, public detail, responsive editor and archive."
            )
            print("Screenshots:", path.resolve())
    finally:
        Product.objects.filter(slug=product_slug).delete()
        Category.objects.filter(slug=category_slug).delete()
        user.delete()
        for name in images:
            if default_storage.exists(name):
                default_storage.delete(name)


if __name__ == "__main__":
    main()
