from celery import shared_task
from django.utils.timezone import now

from berish.models import Berish
from config.telegram import telegram_xabar_yubor
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
    Har 3 soatda ishlaydi (config/celery.py dagi beat_schedule ga qarang).
    To'lanmagan jarimasi bor o'quvchilarga bot orqali eslatma yuboradi:
    «Jarimangizni to'lang va kitobni qaytaring!». Jarima to'languncha takrorlanadi.
    """
    qs = (
        Jarima.objects.filter(tolandimi=False)
        .select_related("berish__oquvchi", "berish__nusxa__kitob")
        .order_by("berish__oquvchi_id")
    )

    oquvchilar = {}
    for jarima in qs:
        oquvchi = jarima.berish.oquvchi
        if not oquvchi.telegram_id:
            continue
        qarz = oquvchilar.setdefault(oquvchi, {"kitoblar": [], "jami": 0})
        qarz["kitoblar"].append(
            {
                "nomi": jarima.berish.nusxa.kitob.nomi,
                "summa": jarima.summa,
                "qaytarilmagan": jarima.berish.qaytarilgan_sana is None,
            }
        )
        qarz["jami"] += jarima.summa

    yuborildi = 0
    for oquvchi, qarz in oquvchilar.items():
        satrlar = []
        for k in qarz["kitoblar"]:
            belgi = "🔴" if k["qaytarilmagan"] else "📕"
            satrlar.append(f"{belgi} 📖 {k['nomi']} — {k['summa']} so'm")

        matn = (
            "⚠️ <b>Jarima eslatmasi!</b>\n\n"
            + "\n".join(satrlar)
            + f"\n\nUmumiy qarz: <b>{qarz['jami']} so'm</b>\n\n"
            + "Iltimos, jarimangizni to'lang va kitobni qaytaring!\n"
            + "To'lovni kutubxonachiga topshiring."
        )
        if telegram_xabar_yubor(oquvchi.telegram_id, matn):
            yuborildi += 1
    return f"{yuborildi} ta o'quvchiga jarima eslatmasi yuborildi"
