from .models import SiteSettings, Category
from django.conf import settings


def site_context(request):
    return {
        "site": SiteSettings.load(),
        "nav_categories": Category.objects.filter(active=True),
        "debug": settings.DEBUG,
        "canonical": settings.SITE_URL + request.path,
        "meta_description": "Explore the KT Naturals catalogue, compare pack sizes and enquire directly about availability.",
        "meta_title": "KT Naturals | Everyday pantry essentials",
        "noindex": bool(request.GET) or request.path.startswith("/owner/"),
    }
