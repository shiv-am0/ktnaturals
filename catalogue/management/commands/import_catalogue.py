"""Import the verified product table from the owner-supplied PDF.

The PDF itself is intentionally not read at runtime (or included in Docker):
its page 2 price table and selected non-medical copy were transcribed into
catalogue.catalogue_source. Existing slugs and owner-edited site settings are
never overwritten. Publishing is restricted to an explicit local preview.
"""

from decimal import Decimal
from io import BytesIO
from textwrap import wrap
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from catalogue.catalogue_source import (
    ABOUT,
    DELIVERY_AREA,
    HOME_INTRO,
    ITEMS,
    PHONE,
    WHATSAPP_DIGITS,
)
from catalogue.models import (
    Category,
    Product,
    ProductImage,
    ProductVariant,
    SiteSettings,
)

CATEGORY_SLUGS = {
    "Cold-Pressed Oils": "cold-pressed-oils",
    "Ghee & Honey": "ghee-honey",
    "Wheat Flours": "wheat-flours",
    "Pantry Staples": "pantry-staples",
}


def placeholder(name):
    """Visibly unfinished image, never represented as product photography."""
    image = Image.new("RGB", (900, 900), "#faf7f0")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((60, 60, 840, 840), radius=30, outline="#214b35", width=5)
    draw.ellipse((355, 145, 545, 335), outline="#63845a", width=10)
    draw.line((448, 294, 448, 207, 502, 169), fill="#63845a", width=10)
    try:
        title_font = ImageFont.truetype("DejaVuSans.ttf", 42)
        brand_font = ImageFont.truetype("DejaVuSerif.ttf", 52)
        note_font = ImageFont.truetype("DejaVuSans.ttf", 25)
    except OSError:
        title_font = ImageFont.load_default(size=42)
        brand_font = ImageFont.load_default(size=52)
        note_font = ImageFont.load_default(size=25)
    draw.text((450, 365), "KT NATURALS", anchor="mm", font=brand_font, fill="#214b35")
    for index, line in enumerate(wrap(name, width=25)):
        draw.text(
            (450, 490 + index * 58), line, anchor="mm", font=title_font, fill="#26332b"
        )
    draw.text(
        (450, 735), "CATALOGUE PLACEHOLDER", anchor="mm", font=note_font, fill="#214b35"
    )
    draw.text(
        (450, 780), "OWNER PHOTO PENDING", anchor="mm", font=note_font, fill="#214b35"
    )
    out = BytesIO()
    image.save(out, "WEBP", quality=82)
    return ContentFile(out.getvalue(), name="placeholder.webp")


class Command(BaseCommand):
    help = (
        "Import 18 owner-PDF catalogue listings without overwriting existing records."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply", action="store_true", help="Confirm local database writes."
        )
        parser.add_argument(
            "--publish-local",
            action="store_true",
            help="Only for a DEBUG local site: publish with labelled photo placeholders and archive published demos.",
        )
        parser.add_argument(
            "--replace-demo-local",
            action="store_true",
            help="With --publish-local, remove only is_demo products, empty demo categories and their unreferenced media.",
        )
        parser.add_argument(
            "--refresh-placeholders-local",
            action="store_true",
            help="Regenerate only unchanged importer-labelled placeholder images on a local DEBUG site.",
        )

    def handle(self, *args, **options):
        if not options["apply"]:
            raise CommandError(
                "Pass --apply after reviewing the PDF transcription and backup."
            )
        publish = options["publish_local"]
        replace_demo = options["replace_demo_local"]
        refresh = options["refresh_placeholders_local"]
        if replace_demo and not publish:
            raise CommandError("--replace-demo-local requires --publish-local.")
        if (publish or refresh) and (
            not settings.DEBUG
            or urlparse(settings.SITE_URL).hostname
            not in {"localhost", "127.0.0.1", "testserver"}
        ):
            raise CommandError(
                "Publishing or refreshing placeholders is restricted to a local DEBUG site."
            )

        created = 0
        skipped = []
        for item in ITEMS:
            slug = slugify(item.name)
            if Product.objects.filter(slug=slug).exists():
                skipped.append(slug)
                continue
            category_slug = CATEGORY_SLUGS[item.category]
            category, _ = Category.objects.get_or_create(
                slug=category_slug, defaults={"name": item.category}
            )
            artwork = placeholder(item.name)  # Process outside the SQLite write lock.
            with transaction.atomic():
                product = Product.objects.create(
                    name=item.name,
                    slug=slug,
                    category=category,
                    short_description=(
                        "Price from the supplied catalogue; confirm the current price "
                        "and availability directly with KT Naturals."
                    ),
                    description=item.description
                    or (
                        "Listed in the KT Naturals catalogue. Ask the owner for current "
                        "product details before ordering."
                    ),
                    featured=item.featured,
                    sort_order=created,
                )
                for order, (label, amount) in enumerate(item.prices):
                    ProductVariant.objects.create(
                        product=product,
                        label=label,
                        price=Decimal(amount),
                        sort_order=order,
                        available=True,
                    )
                photo = ProductImage(
                    product=product,
                    alt_text=f"Catalogue placeholder for {item.name}; owner product photo pending",
                    is_cover=True,
                )
                photo.image.save(f"{slug}-placeholder.webp", artwork, save=True)
                if publish:
                    product.status = "published"
                    product.save()
            created += 1

        if not SiteSettings.objects.exists():
            SiteSettings.objects.create(
                brand_name="KT Naturals",
                home_intro=HOME_INTRO,
                about=ABOUT,
                about_published=True,
                phone=PHONE,
                whatsapp_number=WHATSAPP_DIGITS,
                delivery_area=DELIVERY_AREA,
            )
        if replace_demo:
            with transaction.atomic():
                old_images = list(
                    ProductImage.objects.filter(product__is_demo=True).values_list(
                        "image", flat=True
                    )
                )
                Product.objects.filter(is_demo=True).delete()
                Category.objects.filter(
                    slug__startswith="demo-", products__isnull=True
                ).delete()

                def clear_old_media():
                    storage = ProductImage._meta.get_field("image").storage
                    for name in old_images:
                        if (
                            name
                            and not ProductImage.objects.filter(image=name).exists()
                        ):
                            storage.delete(name)

                transaction.on_commit(clear_old_media)
        elif publish:
            Product.objects.filter(is_demo=True, status="published").update(
                status="archived"
            )
        if refresh:
            refreshed = 0
            source_slugs = {slugify(item.name) for item in ITEMS}
            for photo in ProductImage.objects.select_related("product").filter(
                product__slug__in=source_slugs, is_cover=True
            ):
                expected_alt = f"Catalogue placeholder for {photo.product.name}; owner product photo pending"
                filename = photo.image.name.rsplit("/", 1)[-1]
                if (
                    photo.alt_text != expected_alt
                    or not filename.startswith(photo.product.slug + "-placeholder")
                    or not filename.endswith(".webp")
                    or not photo.image.storage.exists(photo.image.name)
                ):
                    continue
                with photo.image.storage.open(photo.image.name, "wb") as output:
                    output.write(placeholder(photo.product.name).read())
                refreshed += 1
            self.stdout.write(
                f"Refreshed {refreshed} importer-labelled placeholder images."
            )
        self.stdout.write(
            f"Created {created} catalogue products; skipped {len(skipped)} existing slugs "
            f"without database changes; new listings={'local preview' if publish else 'draft'}; "
            "existing site settings preserved."
        )
        if skipped:
            self.stdout.write("Existing slugs preserved: " + ", ".join(skipped))
