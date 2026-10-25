import io
import uuid
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError

MAX_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 20_000_000


def safe_image(upload):
    if upload.size > MAX_BYTES:
        raise ValidationError("Use an image smaller than 8 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            upload.seek(0)
            with Image.open(upload) as check:
                if check.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValidationError(
                        "Use a JPEG, PNG or WebP image; SVG and animated files are not accepted."
                    )
                if check.width * check.height > MAX_PIXELS:
                    raise ValidationError(
                        "Use an image with no more than 20 million pixels."
                    )
                if getattr(check, "is_animated", False):
                    raise ValidationError(
                        "Please use a still photo, not an animated image."
                    )
                check.verify()
            upload.seek(0)
            with Image.open(upload) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
                image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                result = io.BytesIO()
                image.save(result, "WEBP", quality=84, method=6)
        return ContentFile(result.getvalue(), name=f"{uuid.uuid4().hex}.webp")
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise ValidationError(
            "This file is not a safe readable image. Choose a JPEG, PNG or WebP photo."
        )
