from django.urls import path
from django.contrib.auth import views as auth
from . import owner
from .forms import StaffAuthenticationForm

urlpatterns = [
    path("", owner.dashboard, name="owner_dashboard"),
    path(
        "login/",
        auth.LoginView.as_view(
            template_name="owner/login.html",
            authentication_form=StaffAuthenticationForm,
        ),
        name="owner_login",
    ),
    path("logout/", auth.LogoutView.as_view(), name="owner_logout"),
    path(
        "password/",
        owner.staff_required(
            auth.PasswordChangeView.as_view(
                template_name="owner/password.html", success_url="/owner/"
            )
        ),
        name="owner_password",
    ),
    path("products/", owner.product_list, name="owner_products"),
    path("products/new/", owner.product_edit, name="owner_product_new"),
    path("products/<int:pk>/", owner.product_edit, name="owner_product"),
    path("products/<int:pk>/archive/", owner.archive, name="owner_archive"),
    path("products/<int:pk>/preview/", owner.preview, name="owner_preview"),
    path(
        "products/<int:pk>/variants/new/", owner.variant_edit, name="owner_variant_new"
    ),
    path(
        "products/<int:pk>/variants/<int:item_pk>/",
        owner.variant_edit,
        name="owner_variant",
    ),
    path("products/<int:pk>/images/new/", owner.image_edit, name="owner_image_new"),
    path(
        "products/<int:pk>/images/<int:item_pk>/", owner.image_edit, name="owner_image"
    ),
    path(
        "products/<int:pk>/<str:kind>/<int:item_pk>/remove/",
        owner.item_remove,
        name="owner_item_remove",
    ),
    path("categories/", owner.categories, name="owner_categories"),
    path("settings/", owner.settings_edit, name="owner_settings"),
]
