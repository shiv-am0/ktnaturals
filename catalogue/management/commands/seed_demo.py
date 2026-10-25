import io
from decimal import Decimal
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from catalogue.models import Category, Product, ProductVariant, ProductImage

EXAMPLES = [
    ("Ghee", "ghee", "Ghee", ("250 g", "500 g"), ("220", "420"), "#b88936"),
    (
        "Mustard oil",
        "mustard-oil",
        "Oils",
        ("500 ml", "1 L"),
        ("110", "210"),
        "#b39439",
    ),
    (
        "Groundnut oil",
        "groundnut-oil",
        "Oils",
        ("500 ml", "1 L"),
        ("130", "250"),
        "#b79568",
    ),
    (
        "Wheat flour",
        "wheat-flour",
        "Flours",
        ("1 kg", "5 kg"),
        ("65", "310"),
        "#c3ad86",
    ),
    ("Rice flour", "rice-flour", "Flours", ("500 g", "1 kg"), ("50", "95"), "#c6c3a6"),
    (
        "Sesame oil",
        "sesame-oil",
        "Oils",
        ("250 ml", "500 ml"),
        ("120", "230"),
        "#907348",
    ),
]


def illustration(label, tone):
    image = Image.new("RGB", (1000, 1000), "#eeeadf")
    d = ImageDraw.Draw(image)
    d.ellipse((60, 710, 950, 890), fill="#dfdacb")
    d.rounded_rectangle((270, 250, 730, 790), radius=70, fill=tone)
    d.rounded_rectangle((290, 202, 710, 282), radius=18, fill="#214b35")
    d.rounded_rectangle((315, 390, 685, 650), radius=10, fill="#faf7f0")
    try:
        large = ImageFont.truetype("DejaVuSerif.ttf", 44)
        small = ImageFont.truetype("DejaVuSans.ttf", 22)
    except OSError:
        large = small = ImageFont.load_default(size=28)
    d.text((500, 430), "KT NATURALS", font=large, fill="#214b35", anchor="mt")
    d.text((500, 512), label, font=small, fill="#26332b", anchor="mt")
    d.text((500, 566), "ILLUSTRATION · DEMO", font=small, fill="#26332b", anchor="mt")
    d.text(
        (500, 925),
        "DEVELOPMENT EXAMPLE — NOT ACTUAL PACKAGING",
        font=small,
        fill="#26332b",
        anchor="mt",
    )
    out = io.BytesIO()
    image.save(out, "WEBP", quality=85)
    return ContentFile(out.getvalue())


class Command(BaseCommand):
    help = "Create six visibly labelled local demo products. Never overwrites existing slugs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm-local",
            action="store_true",
            help="Confirm this is local development only.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG or not options["confirm_local"]:
            raise CommandError(
                "Demo data requires DEBUG=True and --confirm-local. Never run against production data."
            )
        created = 0
        for name, slug, category, sizes, prices, tone in EXAMPLES:
            if Product.objects.filter(slug="demo-" + slug).exists():
                continue
            cat, _ = Category.objects.get_or_create(
                slug="demo-" + category.lower(), defaults={"name": "Demo · " + category}
            )
            p = Product.objects.create(
                name="Demo · " + name,
                slug="demo-" + slug,
                category=cat,
                is_demo=True,
                featured=True,
                short_description="Development example. Pack sizes and prices are illustrative only.",
                description="DEMO CONTENT — not an actual product offer. Replace with owner-approved product details and real photographs before launch. No sourcing, health or certification claims are made.",
            )
            for index, (size, price) in enumerate(zip(sizes, prices)):
                ProductVariant.objects.create(
                    product=p, label=size, price=Decimal(price), sort_order=index
                )
            photo = ProductImage(
                product=p,
                alt_text="Demo illustration of "
                + name
                + "; not actual product packaging",
                is_cover=True,
            )
            photo.image.save(
                "demo-" + slug + ".webp", illustration(name, tone), save=True
            )
            p.status = "published"
            p.save()
            created += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created} demo products; existing slugs left untouched. No contact number configured."
            )
        )
