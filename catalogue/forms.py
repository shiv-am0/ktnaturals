from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Product, Category, SiteSettings, ProductVariant, ProductImage
from .images import safe_image
from django.core import signing


class StaffAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise forms.ValidationError(
                "This account does not have owner access.", code="invalid_login"
            )


class ProductForm(forms.ModelForm):
    revision = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["revision"].initial = signing.dumps(
                {
                    "pk": self.instance.pk,
                    "updated": self.instance.updated_at.isoformat(),
                },
                salt="edit",
            )

    class Meta:
        model = Product
        exclude = ["is_demo", "created_at", "updated_at"]
        widgets = {
            name: forms.Textarea(attrs={"rows": 4})
            for name in ["description", "ingredients", "storage"]
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"


class SettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        exclude = ["updated_at"]
        widgets = {
            name: forms.Textarea(attrs={"rows": 5})
            for name in ["home_intro", "about", "delivery_returns", "privacy"]
        }


class VariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        exclude = ["product"]


class ImageForm(forms.ModelForm):
    image = forms.FileField(
        help_text="JPEG, PNG or WebP. Up to 8 MB / 20 megapixels. Photos are resized and metadata removed."
    )

    class Meta:
        model = ProductImage
        exclude = ["product"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].required = not bool(self.instance.pk)

    def clean_image(self):
        value = self.cleaned_data.get("image")
        if (
            value
            and hasattr(value, "temporary_file_path")
            or value
            and hasattr(value, "content_type")
        ):
            return safe_image(value)
        return self.instance.image if self.instance.pk else value
