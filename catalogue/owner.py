from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .models import Product, Category, SiteSettings
from .forms import ProductForm, CategoryForm, SettingsForm, VariantForm, ImageForm
from .models import ProductVariant, ProductImage
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core import signing
from django.db.models import F


def remove_unreferenced_photo(name):
    """Delete obsolete public media only after the database change commits."""
    if name and not ProductImage.objects.filter(image=name).exists():
        ProductImage._meta.get_field("image").storage.delete(name)


def product_revision(product):
    return signing.dumps(
        {"pk": product.pk, "updated": product.updated_at.isoformat()}, salt="edit"
    )


def verify_product_revision(product, token):
    try:
        revision = signing.loads(token, salt="edit")
        if revision.get("pk") == product.pk and Product.objects.filter(
            pk=product.pk, updated_at=revision.get("updated")
        ).update(updated_at=F("updated_at")):
            return
    except signing.BadSignature:
        pass
    raise ValidationError(
        "This product changed since you opened the editor. Reload and review your changes before saving."
    )


def content_revision(record):
    fields = {
        field.name: getattr(record, field.attname)
        for field in record._meta.fields
        if field.editable
    }
    return signing.dumps(
        {"model": record._meta.label, "pk": record.pk, "fields": fields},
        salt="content-edit",
    )


def verify_content_revision(record, token):
    try:
        if signing.loads(token, salt="content-edit") == signing.loads(
            content_revision(record), salt="content-edit"
        ):
            return
    except signing.BadSignature:
        pass
    raise ValidationError(
        "This content changed since you opened the editor. Reload and review your changes before saving."
    )


def staff_required(view):
    @wraps(view)
    def protected(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), "/owner/login/")
        if not request.user.is_active or not request.user.is_staff:
            raise PermissionDenied
        response = view(request, *args, **kwargs)
        response["X-Robots-Tag"] = "noindex, nofollow"
        response["Cache-Control"] = "no-store, private"
        return response

    return protected


@staff_required
def dashboard(request):
    return render(
        request,
        "owner/dashboard.html",
        {
            "published": Product.objects.filter(status="published").count(),
            "drafts": Product.objects.filter(status="draft").count(),
            "archived": Product.objects.filter(status="archived").count(),
            "recent": Product.objects.order_by("-updated_at")[:5],
        },
    )


@staff_required
def product_list(request):
    return render(request, "owner/products.html", {"products": Product.objects.all()})


@staff_required
def product_edit(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else Product()
    form = ProductForm(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                if product.pk:
                    try:
                        revision = signing.loads(
                            form.cleaned_data["revision"], salt="edit"
                        )
                    except signing.BadSignature:
                        raise ValidationError(
                            "This product changed since you opened the editor. Reload and review your changes before saving."
                        )
                    from django.db.models import F

                    if revision.get("pk") != product.pk or not Product.objects.filter(
                        pk=product.pk, updated_at=revision.get("updated")
                    ).update(updated_at=F("updated_at")):
                        raise ValidationError(
                            "This product changed since you opened the editor. Reload and review your changes before saving."
                        )
                product = form.save()
            messages.success(request, "Product saved.")
            return redirect("owner_product", pk=product.pk)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, "owner/product.html", {"form": form, "product": product})


@staff_required
def archive(request, pk):
    p = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        try:
            with transaction.atomic():
                verify_product_revision(p, request.POST.get("revision", ""))
                p.status = "archived"
                p.save()
            messages.success(request, "Product archived. Nothing was deleted.")
            return redirect("owner_products")
        except ValidationError as exc:
            return render(
                request,
                "owner/confirm.html",
                {
                    "product": p,
                    "error": str(exc),
                    "revision": request.POST.get("revision", ""),
                },
            )
    return render(
        request, "owner/confirm.html", {"product": p, "revision": product_revision(p)}
    )


@staff_required
def preview(request, pk):
    p = get_object_or_404(Product, pk=pk)
    return render(
        request,
        "product_detail.html",
        {"product": p, "variants": p.active_variants, "preview": True},
    )


@staff_required
def categories(request):
    obj = (
        get_object_or_404(Category, pk=request.GET["edit"])
        if request.GET.get("edit")
        else Category()
    )
    form = CategoryForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                if obj.pk:
                    verify_content_revision(
                        Category.objects.get(pk=obj.pk),
                        request.POST.get("revision", ""),
                    )
                form.save()
            messages.success(request, "Category saved.")
            return redirect("owner_categories")
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(
        request,
        "owner/categories.html",
        {
            "form": form,
            "categories": Category.objects.all(),
            "editing": obj.pk,
            "revision": request.POST.get("revision", "")
            if request.method == "POST"
            else content_revision(obj)
            if obj.pk
            else "",
        },
    )


@staff_required
def settings_edit(request):
    obj = SiteSettings.load()
    form = SettingsForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                if obj.pk:
                    verify_content_revision(
                        SiteSettings.objects.get(pk=obj.pk),
                        request.POST.get("revision", ""),
                    )
                form.save()
            messages.success(request, "Website settings saved.")
            return redirect("owner_settings")
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(
        request,
        "owner/settings.html",
        {
            "form": form,
            "revision": request.POST.get("revision", "")
            if request.method == "POST"
            else content_revision(obj)
            if obj.pk
            else "",
        },
    )


@staff_required
def variant_edit(request, pk, item_pk=None):
    p = get_object_or_404(Product, pk=pk)
    item = (
        get_object_or_404(ProductVariant, pk=item_pk, product=p)
        if item_pk
        else ProductVariant(product=p)
    )
    form = VariantForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                if item.pk:
                    verify_product_revision(p, request.POST.get("revision", ""))
                form.save()
                p.save()
            messages.success(request, "Pack size saved.")
            return redirect("owner_product", pk=p.pk)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(
        request,
        "owner/item.html",
        {
            "form": form,
            "product": p,
            "kind": "pack size",
            "item": item,
            "revision": product_revision(p),
        },
    )


@staff_required
def image_edit(request, pk, item_pk=None):
    p = get_object_or_404(Product, pk=pk)
    item = (
        get_object_or_404(ProductImage, pk=item_pk, product=p)
        if item_pk
        else ProductImage(product=p)
    )
    form = ImageForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                if item.pk:
                    verify_product_revision(p, request.POST.get("revision", ""))
                previous_name = (
                    ProductImage.objects.filter(pk=item.pk)
                    .values_list("image", flat=True)
                    .first()
                    if item.pk
                    else None
                )
                if form.cleaned_data["is_cover"]:
                    p.images.exclude(pk=item.pk).update(is_cover=False)
                form.save()
                p.save()
                if previous_name and previous_name != item.image.name:
                    transaction.on_commit(
                        lambda name=previous_name: remove_unreferenced_photo(name)
                    )
            messages.success(request, "Photo saved.")
            return redirect("owner_product", pk=p.pk)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(
        request,
        "owner/item.html",
        {
            "form": form,
            "product": p,
            "kind": "photo",
            "item": item,
            "revision": product_revision(p),
        },
    )


@staff_required
def item_remove(request, pk, kind, item_pk):
    p = get_object_or_404(Product, pk=pk)
    model = ProductVariant if kind == "variants" else ProductImage
    item = get_object_or_404(model, pk=item_pk, product=p)
    error = None
    if request.method == "POST":
        try:
            with transaction.atomic():
                old_photo_name = item.image.name if kind == "images" else None
                item.delete()
                p.save()
                if old_photo_name:
                    transaction.on_commit(
                        lambda name=old_photo_name: remove_unreferenced_photo(name)
                    )
            messages.success(request, "Item removed.")
            return redirect("owner_product", pk=p.pk)
        except ValidationError:
            error = "A published product needs an active size and a cover photo. Save the product as draft first, or add a replacement."
    return render(
        request,
        "owner/remove.html",
        {"product": p, "item": item, "kind": kind, "error": error},
    )
