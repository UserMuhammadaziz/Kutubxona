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
    bugun = now().date()
    nishon_sana = bugun + timedelta(days=settings.ESLATMA_KUNLAR_OLDIN)
    # Sana ANIQ tengligi bilan emas, oyna (range) bilan izlanadi. Aks holda
    # celery beat kechiksa yoki server o'sha kuni o'chib qolsa, o'sha kuni
    # yuborilmagan eslatma butunlay o'tib ketardi: belgi qo'yilmagan bo'lsa
    # ham, keyingi chaqiruvda nishon_sana boshqacha bo'lgani uchun berish
    # qayta topilmasdi.
    qs = (
        Berish.objects.select_related("oquvchi", "nusxa", "kitob")
        .filter(
            qaytarish_muddati__lte=nishon_sana,
            qaytarish_muddati__gte=nishon_sana - timedelta(days=5),
            qaytarilgan_sana__isnull=True,
            eslatma_yuborilgan=False,
        )
    )

    yuborildi = 0
    for berish in qs.iterator():
        oquvchi = berish.oquvchi
        if not oquvchi.telegram_id:
            # Telegramga bog'lanmagan o'quvchiga eslatma yuborib bo'lmaydi —
            # belgi qo'ymay qoldiramiz, kelgusi haftada ham tekshiriladi.
            continue

        qolgan = (berish.qaytarish_muddati - bugun).days
        if berish.nusxa_id:
            manzil = f"Inventar raqami: {berish.nusxa.inventar_raqami}"
        else:
            manzil = "Nusxasi yo'q — kitob aslida berilgan"
        if qolgan < 0:
            # Oyna tufayli kechikkan holat bo'lishi mumkin — "yaqinlashmoqda"
            # emas, "o'tib ketdi" deb aytamiz.
            sarlavha = "🔴 <b>Qaytarish muddati o'tib ketdi!</b>"
            qolgan_matni = (
                f"Muddati <b>{abs(qolgan)} kun</b> oldin o'tgan — jarima "
                "belgilanishi mumkin."
            )
        else:
            sarlavha = "⏰ <b>Qaytarish muddati yaqinlashmoqda!</b>"
            qolgan_matni = f"Qolgan kun: <b>{qolgan}</b>"
        matn = (
            f"{sarlavha}\n\n"
            f"📖 <b>{telegram_escape(berish.kitob.nomi)}</b>\n"
            f"{manzil}\n"
            f"Qaytarish muddati: <b>{berish.qaytarish_muddati}</b>\n"
            f"{qolgan_matni}\n\n"
            "Iltimos, vaqtida kutubxonaga qaytaring!"
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
