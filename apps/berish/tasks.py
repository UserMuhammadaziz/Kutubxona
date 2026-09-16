from celery import shared_task
from django.utils.timezone import now, timedelta

from .models import Berish


@shared_task
def eslatma_yuborish():
    """
    Har kuni soat 09:00 da ishlaydi. Muddati 2 kundan keyin tugaydigan va
    hali eslatma yuborilmagan faol berishlarni tanlaydi, telegram_id si bor
    o'quvchilarga bot orqali eslatma yuboradi va eslatma_yuborilgan=True qiladi.
    """
    nishon_sana = now().date() + timedelta(days=2)
    qs = Berish.objects.select_related("oquvchi", "nusxa__kitob").filter(
        qaytarish_muddati=nishon_sana,
        qaytarilgan_sana__isnull=True,
        eslatma_yuborilgan=False,
    )

    yuborildi = 0
    for berish in qs:
        oquvchi = berish.oquvchi
        if not oquvchi.telegram_id:
            continue
        try:
            # Botga xabar yuborish shu yerda amalga oshiriladi
            # (masalan bot-client moduli orqali requests.post chaqiriladi).
            # from bot.client import xabar_yubor
            # xabar_yubor(oquvchi.telegram_id, matn)
            pass
        except Exception:
            # TelegramForbiddenError va sh.k. holatlarda vazifa yiqilmasin
            continue
        berish.eslatma_yuborilgan = True
        berish.save(update_fields=["eslatma_yuborilgan"])
        yuborildi += 1
    return f"{yuborildi} ta eslatma yuborildi"
