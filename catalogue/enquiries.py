import re
from urllib.parse import urlencode
from django.core import signing
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import SiteSettings


def snapshot(product):
    return {
        "product": product.pk,
        "name": product.name,
        "slug": product.slug,
        "updated": product.updated_at.isoformat(),
        "number": SiteSettings.load().whatsapp_number,
        "variants": [
            (v.pk, v.label, str(v.price), v.available) for v in product.active_variants
        ],
    }


def quote_for(product):
    return signing.dumps(snapshot(product), salt="enquiry")


def quote_current(product, token):
    try:
        return signing.loads(token, salt="enquiry", max_age=86400) == signing.loads(
            quote_for(product), salt="enquiry"
        )
    except signing.BadSignature:
        return False


def enquiry_link(product, variant, quantity):
    number = SiteSettings.load().whatsapp_number
    if not re.fullmatch(r"[1-9][0-9]{7,14}", number):
        raise ValidationError(
            "Enquiries are not available yet. Please use the contact page."
        )
    text = f"Hello KT Naturals! I would like to enquire about:\nProduct: {product.name}\nPack size: {variant.label}\nQuantity: {quantity}\nListed unit price: ₹{variant.price:.2f}\nProduct link: {settings.SITE_URL}{product.get_absolute_url()}\nPlease confirm availability, delivery charges, and payment details."
    return "https://wa.me/" + number + "?" + urlencode({"text": text})
