from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils.timezone import now

from berish.models import Berish
from config.telegram import telegram_escape, telegram_xabar_yubor
from .models import Jarima
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


@shared_task
def jarima_eslatma_yubor():
    """
    Har 3 soatda chaqiriladi (config/celery.py dagi beat_schedule ga qarang).
    To'lanmagan jarimasi bor o'quvchilarga bot orqali eslatma yuboradi.

    Takroriy xabar yuborilmasligi uchun: har bir o'quvchiga so'nggi eslatma
    yuborilganiga JARIMA_ESLATMA_TAKROR_SOAT (standart 24 soat) o'tmagan
    bo'lsa, bu chaqiruvda o'shanda skip qilinadi. Eslatma yuborilgan sanasi
    Jarima.eslatma_yuborilgan_sana da saqlanadi.
    """
    qarz = (
        Jarima.objects.filter(tolandimi=False)
        .select_related("berish__oquvchi", "berish__nusxa__kitob")
        .order_by("berish__oquvchi_id")
    )

    oquvchilar = {}
    eng_yaqin_sana = {}
    for jarima in qarz.iterator():
        oquvchi = jarima.berish.oquvchi
        if not oquvchi.telegram_id:
            continue

        hisob = oquvchilar.setdefault(oquvchi, {"jarimalar": [], "jami": 0})
        hisob["jarimalar"].append(
            {
                "nomi": jarima.berish.nusxa.kitob.nomi,
                "summa": jarima.summa,
                "qaytarilmagan": jarima.berish.qaytarilgan_sana is None,
            }
        )
        hisob["jami"] += jarima.summa

        # Bu o'quvchining barcha jarimalari bo'yicha eng so'nggi eslatma sanasi.
        oldingi = jarima.eslatma_yuborilgan_sana
        if oldingi is not None and (
            eng_yaqin_sana.get(oquvchi) is None or oldingi > eng_yaqin_sana[oquvchi]
        ):
            eng_yaqin_sana[oquvchi] = oldingi

    yuborildi = 0
    for oquvchi, ma in oquvchilar.items():
        # Takroriy xabar bo'lmasligi uchun: o'quvchiga so'nggi eslatma
        # yuborilganiga takror_muddat o'tmagan bo'lsa, butun o'quvchi
        # skip qilinadi (jarimalar bir-biriga qarama-qarshi emas).
        eng_yaqin = eng_yaqin_sana.get(oquvchi)
        if eng_yaqin is not None:
            takror_muddat = timedelta(hours=settings.JARIMA_ESLATMA_TAKROR_SOAT)
            if eng_yaqin > now() - takror_muddat:
                continue

        satrlar = []
        for k in ma["jarimalar"]:
            belgi = "🔴" if k["qaytarilmagan"] else "📕"
            # Kitob nomi Telegram HTML parse_mode da teglarni buzsa, butun
            # xabar yuborilmay qoladi — shuning uchun escape qilamiz.
            satrlar.append(f"{belgi} 📖 {telegram_escape(k['nomi'])} — {k['summa']} so'm")

        matn = (
            "⚠️ <b>Jarima eslatmasi!</b>\n\n"
            + "\n".join(satrlar)
            + f"\n\nUmumiy qarz: <b>{ma['jami']} so'm</b>\n\n"
            + "Iltimos, jarimangizni to'lang va kitobni qaytaring!\n"
            + "To'lovni kutubxonachiga topshiring."
        )

        yuborish_vaqti = now()
        if not telegram_xabar_yubor(oquvchi.telegram_id, matn):
            continue

        # Yuborildi — kelgori uchun sanani belgilaymiz, shunda keyingi
        # chaqiruvlar (3 soatlik) takroriy xabar yubormaydi.
        Jarima.objects.filter(
            berish__oquvchi=oquvchi, tolandimi=False
        ).update(eslatma_yuborilgan_sana=yuborish_vaqti)
        yuborildi += 1

    return f"{yuborildi} ta o'quvchiga jarima eslatmasi yuborildi"
