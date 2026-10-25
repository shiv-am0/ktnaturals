from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, Category, SiteSettings
from .seo import product_schema
from django.conf import settings
from django.http import HttpResponse
from django.utils.html import escape
from .enquiries import quote_for, quote_current, enquiry_link
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.core.exceptions import ValidationError


def public_products():
    return (
        Product.objects.filter(status="published")
        .filter(Q(category__isnull=True) | Q(category__active=True))
        .prefetch_related("variants", "images")
        .select_related("category")
    )


def home(request):
    return render(
        request, "home.html", {"products": public_products().filter(featured=True)[:4]}
    )


def products(request, slug=None):
    category = get_object_or_404(Category, slug=slug, active=True) if slug else None
    items = public_products()
    query = request.GET.get("q", "").strip()[:100]
    if category:
        items = items.filter(category=category)
    if request.GET.get("category"):
        items = items.filter(category__slug=request.GET["category"])
    if query:
        items = items.filter(
            Q(name__icontains=query) | Q(short_description__icontains=query)
        )
    category_description = (
        (
            category.seo_description
            or category.description
            or f"Browse {category.name} products at KT Naturals. See pack sizes and listed INR prices."
        )
        if category
        else None
    )
    return render(
        request,
        "products.html",
        {
            "products": items,
            "category": category,
            "query": query,
            "meta_title": (
                category.seo_title or category.name + " products | KT Naturals"
            )
            if category
            else "Products | KT Naturals",
            "meta_description": category_description
            or "Browse our pantry essentials. See available pack sizes, listed INR prices and enquire directly with KT Naturals.",
        },
    )


def product_detail(request, slug):
    p = get_object_or_404(public_products(), slug=slug)
    return render(
        request,
        "product_detail.html",
        {
            "product": p,
            "quote": quote_for(p),
            "variants": p.active_variants,
            "meta_title": p.seo_title or p.name + " | KT Naturals",
            "meta_description": p.seo_description
            or p.short_description
            or "Explore "
            + p.name
            + " pack sizes and current listed prices at KT Naturals.",
            "social_image": settings.SITE_URL + p.cover.image.url if p.cover else None,
            "schema": product_schema(p),
            "related": public_products()
            .filter(category=p.category)
            .exclude(pk=p.pk)[:3],
        },
    )


@require_POST
def enquiry(request, slug):
    p = get_object_or_404(public_products(), slug=slug)
    try:
        raw = request.POST.get("quantity", "")
        if (
            not raw.isascii()
            or not raw.isdigit()
            or len(raw) > 2
            or not 1 <= int(raw) <= 99
        ):
            raise ValidationError("Choose a whole-number quantity from 1 to 99.")
        quantity = int(raw)
        variant = p.active_variants.filter(
            pk=request.POST.get("variant", "0"), available=True
        ).first()
        if not variant:
            raise ValidationError(
                "That pack size is unavailable. Please choose an available size."
            )
        link = enquiry_link(p, variant, quantity)
    except (ValidationError, ValueError) as exc:
        message = (
            " ".join(exc.messages)
            if isinstance(exc, ValidationError)
            else "Choose a valid pack size."
        )
        return render(
            request, "enquiry_error.html", {"product": p, "error": message}, status=400
        )
    if not quote_current(p, request.POST.get("quote", "")):
        return render(
            request,
            "enquiry_confirm.html",
            {
                "product": p,
                "variant": variant,
                "quantity": quantity,
                "quote": quote_for(p),
            },
        )
    return HttpResponseRedirect(link)


def information(request, page):
    site = SiteSettings.load()
    titles = {
        "about": "Our story",
        "contact": "Let’s talk",
        "delivery-returns": "Delivery & returns",
        "privacy": "Your privacy",
    }
    field = {
        "about": "about",
        "delivery-returns": "delivery_returns",
        "privacy": "privacy",
    }.get(page)
    content = (
        getattr(site, field) if field and getattr(site, field + "_published") else ""
    )
    return render(
        request,
        "information.html",
        {
            "page": page,
            "heading": titles[page],
            "content": content,
            "noindex": bool(field and not content) or bool(request.GET),
            "meta_title": titles[page] + " | KT Naturals",
            "meta_description": {
                "about": "Meet KT Naturals. Read our owner-approved brand story and product information.",
                "contact": "Contact KT Naturals with product questions, availability and delivery enquiries.",
                "delivery-returns": "Delivery and returns information for KT Naturals. Confirm details directly with the owner.",
                "privacy": "Privacy information for the KT Naturals website.",
            }[page],
        },
    )


def sitemap(request):
    site = SiteSettings.load()
    paths = ["/", "/products/", "/contact/"]
    for path, field in (
        ("/about/", "about"),
        ("/delivery-returns/", "delivery_returns"),
        ("/privacy/", "privacy"),
    ):
        if getattr(site, field + "_published") and getattr(site, field).strip():
            paths.append(path)
    paths += [
        "/categories/" + c.slug + "/" for c in Category.objects.filter(active=True)
    ]
    paths += [p.get_absolute_url() for p in public_products()]
    body = (
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(
            "<url><loc>" + escape(settings.SITE_URL + path) + "</loc></url>"
            for path in paths
        )
        + "</urlset>"
    )
    return HttpResponse(body, content_type="application/xml")


def robots(request):
    return HttpResponse(
        "User-agent: *\nDisallow: /owner/\nDisallow: /admin/\nSitemap: "
        + settings.SITE_URL
        + "/sitemap.xml\n",
        content_type="text/plain",
    )
