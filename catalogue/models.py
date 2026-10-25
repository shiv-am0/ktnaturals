from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    display_order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    seo_title = models.CharField(
        max_length=70, blank=True, help_text="Aim for 50–60 characters."
    )
    seo_description = models.CharField(
        max_length=170, blank=True, help_text="Aim for 140–160 characters."
    )

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    STATUS = [("draft", "Draft"), ("published", "Published"), ("archived", "Archived")]
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="products",
    )
    short_description = models.CharField(max_length=250, blank=True)
    description = models.TextField(blank=True)
    ingredients = models.TextField(blank=True)
    storage = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default="draft")
    featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    seo_title = models.CharField(
        max_length=70, blank=True, help_text="Aim for 50–60 characters."
    )
    seo_description = models.CharField(
        max_length=170, blank=True, help_text="Aim for 140–160 characters."
    )
    is_demo = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.status == "published":
            if (
                not self.pk
                or not self.variants.filter(active=True, price__gte=0).exists()
                or not self.images.filter(is_cover=True).exists()
            ):
                raise ValidationError(
                    "To publish, add at least one active priced pack size and a cover image first."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("product_detail", args=[self.slug])

    @property
    def cover(self):
        return self.images.filter(is_cover=True).first()

    @property
    def active_variants(self):
        return self.variants.filter(active=True)

    @property
    def price_display(self):
        variants = self.active_variants
        available_prices = list(
            variants.filter(available=True).values_list("price", flat=True)
        )
        prices = available_prices or list(variants.values_list("price", flat=True))
        if not prices:
            return "Price to be confirmed"
        prefix = "From " if min(prices) != max(prices) else ""
        return f"{prefix}₹{min(prices):,.2f}"

    @property
    def available(self):
        return self.active_variants.filter(available=True).exists()


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants"
    )
    label = models.CharField(max_length=100)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    active = models.BooleanField(default=True)
    available = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0), name="variant_price_nonnegative"
            )
        ]

    def __str__(self):
        return self.label


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200)
    is_cover = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=models.Q(is_cover=True),
                name="one_cover_per_product",
            )
        ]


class SiteSettings(models.Model):
    brand_name = models.CharField(max_length=80, default="KT Naturals")
    home_intro = models.TextField(blank=True)
    whatsapp_number = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                r"^[1-9][0-9]{7,14}$",
                "Use 8–15 digits including country code, without + or spaces.",
            )
        ],
    )
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    instagram = models.URLField(blank=True)
    location = models.CharField(max_length=250, blank=True)
    opening_hours = models.CharField(max_length=250, blank=True)
    delivery_area = models.CharField(max_length=250, blank=True)
    about = models.TextField(blank=True)
    delivery_returns = models.TextField(blank=True)
    privacy = models.TextField(blank=True)
    about_published = models.BooleanField(default=False)
    delivery_returns_published = models.BooleanField(default=False)
    privacy_published = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        return cls.objects.first() or cls()

    def save(self, *args, **kwargs):
        self.pk = 1
        self.full_clean()
        return super().save(*args, **kwargs)
