from celery import shared_task
from django.conf import settings
from django.utils.timezone import now, timedelta

from config.telegram import telegram_escape, telegram_xabar_yubor
from .models import Berish


@shared_task
def eslatma_yuborish():
    """
    Har kuni soat 09:00 da ishlaydi. Muddati 2 kundan keyin tugaydigan va
    hali eslatma yuborilmagan faol berishlarni tanlaydi, telegram_id si bor
    o'quvchilarga bot orqali eslatma yuboradi va eslatma_yuborilgan=True qiladi.

    Takroriy xabar bo'lmasligi uchun ikki daravali himoya:
      1) eslatma_yuborilgan=False filtr — bir marta yuborilgan berish qayta
         tanlanmaydi;
      2) yuborish muvaffaqiyatli bo'lgandagina belgi qo'yiladi — Telegram
         yuborilmasa, keyingi kunda qayta urinishadi.
    """
    nishon_sana = now().date() + timedelta(days=settings.ESLATMA_KUNLAR_OLDIN)
    qs = Berish.objects.select_related("oquvchi", "nusxa", "kitob").filter(
        qaytarish_muddati=nishon_sana,
        qaytarilgan_sana__isnull=True,
        eslatma_yuborilgan=False,
    )

    yuborildi = 0
    for berish in qs.iterator():
        oquvchi = berish.oquvchi
        if not oquvchi.telegram_id:
            # Telegramga bog'lanmagan o'quvchiga eslatma yuborib bo'lmaydi —
            # belgi qo'ymay qoldiramiz, kelgusi haftada ham tekshiriladi.
            continue

        qolgan = (berish.qaytarish_muddati - now().date()).days
        if berish.nusxa_id:
            manzil = f"Inventar raqami: {berish.nusxa.inventar_raqami}"
        else:
            manzil = "Nusxasi yo'q — kitob aslida berilgan"
        matn = (
            "⏰ <b>Qaytarish muddati yaqinlashmoqda!</b>\n\n"
            f"📖 <b>{telegram_escape(berish.kitob.nomi)}</b>\n"
            f"{manzil}\n"
            f"Qaytarish muddati: <b>{berish.qaytarish_muddati}</b>\n"
            f"Qolgan kun: <b>{qolgan}</b>\n\n"
            "Iltimos, vaqtida kutubxonaga qaytaring! Kechikdirilsa jarima "
            "belgilanishi mumkin."
        )

        try:
            yuborildi_hali = telegram_xabar_yubor(oquvchi.telegram_id, matn)
        except Exception:
            # TelegramForbiddenError va sh.k. holatlarda vazifa yiqilmasin
            continue

        if yuborildi_hali:
            berish.eslatma_yuborilgan = True
            berish.save(update_fields=["eslatma_yuborilgan"])
            yuborildi += 1

    return f"{yuborildi} ta eslatma yuborildi"
