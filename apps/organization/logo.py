"""Safe logo upload: only raster images, re-encoded to a small WebP.

The uploaded bytes are never served as-is. Pillow decodes the image,
which rejects files that only pretend to be images, and the result is
written again as WebP, which strips metadata and any embedded payload.
SVG is not accepted because it can carry scripts.
"""
import hashlib
import io
import re
from pathlib import Path

from django.conf import settings
from PIL import Image, UnidentifiedImageError

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_SOURCE_PIXELS = 4000 * 4000
OUTPUT_SIZE = 512
ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP", "GIF"}
LOGO_DIR = "logos"
LOGO_NAME = re.compile(r"^org(\d+)-[0-9a-f]{12}\.webp$")


class LogoError(ValueError):
    pass


def logo_root() -> Path:
    return Path(settings.MEDIA_ROOT) / LOGO_DIR


def process_logo(upload) -> bytes:
    if upload.size > MAX_UPLOAD_BYTES:
        raise LogoError("Logo hajmi 2 MB dan oshmasligi kerak.")
    data = upload.read()
    try:
        with Image.open(io.BytesIO(data)) as probe:
            fmt = probe.format
            width, height = probe.size
            probe.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise LogoError("Fayl rasm emas yoki buzilgan. PNG, JPG yoki WEBP yuklang.")
    if fmt not in ALLOWED_FORMATS:
        raise LogoError("Faqat PNG, JPG, WEBP yoki GIF rasm yuklash mumkin.")
    if width * height > MAX_SOURCE_PIXELS:
        raise LogoError("Rasm o'lchami juda katta (4000×4000 dan kichik bo'lsin).")
    with Image.open(io.BytesIO(data)) as image:
        image.seek(0)
        image = image.convert("RGBA")
        image.thumbnail((OUTPUT_SIZE, OUTPUT_SIZE))
        out = io.BytesIO()
        image.save(out, format="WEBP", quality=88, method=4)
    return out.getvalue()


def save_logo(organization, upload) -> str:
    """Store the processed logo and return its public URL path."""
    content = process_logo(upload)
    root = logo_root()
    root.mkdir(parents=True, exist_ok=True)
    name = f"org{organization.pk}-{hashlib.sha256(content).hexdigest()[:12]}.webp"
    (root / name).write_bytes(content)
    remove_old_logos(organization, keep=name)
    return f"{settings.MEDIA_URL}{LOGO_DIR}/{name}"


def remove_old_logos(organization, keep: str | None = None) -> None:
    root = logo_root()
    if not root.is_dir():
        return
    for path in root.glob(f"org{organization.pk}-*.webp"):
        if path.name != keep:
            path.unlink(missing_ok=True)
