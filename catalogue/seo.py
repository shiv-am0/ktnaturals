import json
from django.conf import settings
from django.utils.safestring import mark_safe


def product_schema(product):
    url = settings.SITE_URL + product.get_absolute_url()
    node = {
        "@type": "Product",
        "name": product.name,
        "description": product.description or product.short_description,
        "url": url,
        "image": [settings.SITE_URL + i.image.url for i in product.images.all()],
        "offers": [
            {
                "@type": "Offer",
                "name": v.label,
                "price": str(v.price),
                "priceCurrency": "INR",
                "availability": "https://schema.org/InStock"
                if v.available
                else "https://schema.org/OutOfStock",
                "url": url,
            }
            for v in product.active_variants
        ],
    }
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            node,
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Home",
                        "item": settings.SITE_URL + "/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "Products",
                        "item": settings.SITE_URL + "/products/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": product.name,
                        "item": url,
                    },
                ],
            },
        ],
    }
    return mark_safe(
        json.dumps(graph, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
