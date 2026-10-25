from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from catalogue import views

urlpatterns = [
    path("about/", views.information, {"page": "about"}, name="about"),
    path("contact/", views.information, {"page": "contact"}, name="contact"),
    path(
        "delivery-returns/",
        views.information,
        {"page": "delivery-returns"},
        name="delivery_returns",
    ),
    path("privacy/", views.information, {"page": "privacy"}, name="privacy"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
    path("robots.txt", views.robots, name="robots"),
    path("owner/", include("catalogue.owner_urls")),
    path("", views.home, name="home"),
    path("products/", views.products, name="products"),
    path("categories/<slug:slug>/", views.products, name="category"),
    path("products/<slug:slug>/enquire/", views.enquiry, name="enquiry"),
    path("products/<slug:slug>/", views.product_detail, name="product_detail"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
