import base64
import hashlib

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _fernet():
    try:
        from cryptography.fernet import Fernet
    except ImportError as xato:  # pragma: no cover
        raise ImproperlyConfigured(
            "Bot tokenlarini shifrlash uchun `cryptography` paketini o'rnating."
        ) from xato

    kalit = (getattr(settings, "BOT_TOKEN_ENCRYPTION_KEY", "") or "").strip()
    if not kalit:
        if settings.DEBUG:
            # Faqat development uchun qulaylik. Productionda alohida kalit shart.
            kalit = settings.SECRET_KEY
        else:
            raise ImproperlyConfigured(
                "BOT_TOKEN_ENCRYPTION_KEY sozlamasi majburiy (production)."
            )
    xom = kalit.encode("utf-8")
    try:
        return Fernet(xom)
    except (ValueError, TypeError):
        # Kalit Fernet formatida bo'lmasa, barqaror hosil qilamiz.
        return Fernet(base64.urlsafe_b64encode(hashlib.sha256(xom).digest()))


def shifrla(matn):
    return _fernet().encrypt(str(matn).encode("utf-8")).decode("utf-8")


def deshifrla(shifr):
    return _fernet().decrypt(str(shifr).encode("utf-8")).decode("utf-8")
