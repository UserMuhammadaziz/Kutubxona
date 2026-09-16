from celery import shared_task
from django.utils.timezone import now

from berish.models import Berish
from .services import jarimani_hisobla


@shared_task
def jarimalarni_hisobla():
    """
    Har kuni 00:30 da ishlaydi (config/celery.py dagi beat_schedule ga qarang).
    Muddati o'tgan, hali qaytarilmagan va jarimasi to'lanmagan barcha faol
    berishlar uchun jarimani qayta hisoblaydi. Idempotent: bir necha marta
    ketma-ket ishga tushirilsa ham natija o'zgarmaydi, chunki hisoblash
    mantig'i jarima/services.py dagi bitta funksiyada (update_or_create bilan).
    """
    bugun = now().date()
    qs = Berish.objects.filter(
        qaytarilgan_sana__isnull=True,
        qaytarish_muddati__lt=bugun,
    ).exclude(jarima__tolandimi=True)

    yangilangan = 0
    for berish in qs:
        if jarimani_hisobla(berish) is not None:
            yangilangan += 1
    return f"{yangilangan} ta berish uchun jarima yangilandi"
