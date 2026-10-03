from celery import shared_task
from django.db.models import Q
from django.utils.timezone import now

from .models import Navbat
from .services import (
    navbatni_mavjud_nusxa_bilan_ishga_tushir,
    taklifni_bekor_qil_va_keyingisiga_ut,
)


@shared_task
def ochiq_navbatlarni_tekshir():
    """Har 10 daqiqada ishlaydi. Navbatda turgan kitob endi mavjud bo'lsa
    (nusxa qo'shildi, ta'mirdan chiqdi, «asli» kitob qaytarildi yoki holatni
    qo'lda o'zgartirildi), unga taklif yuboradi.

    Bu vazifa «o'lik chorak» holatini butunlay yo'q qiladi: navbatga turgan
    o'quvchi hech qanday xabar olmay qolmasligi kerak. Nusxa qo'shish va
    qaytarish o'zlari ham taklif yuboradi — bu vazifa qolgan yo'llarni
    (masalan, qo'lda holat o'zgartirish) yopadi."""
    ochiq_kitoblar = (
        Navbat.objects.filter(holati="kutmoqda")
        .values_list("kitob_id", flat=True)
        .distinct()
    )
    soni = 0
    for kitob_id in list(ochiq_kitoblar):
        try:
            if navbatni_mavjud_nusxa_bilan_ishga_tushir(kitob_id):
                soni += 1
        except Exception:
            continue
    return f"{soni} ta ochiq navbatga taklif yuborildi"


@shared_task
def takliflarni_tekshir():
    """
    Har 10 daqiqada ishlaydi. settings.TAKLIF_SOAT soatlik javob muddati
    o'tib ketgan takliflarni bekor qiladi (bekor_sababi='muddat_otdi') va
    nusxani navbatdagi keyingi odamga taklif qiladi (Telegram xabari
    services.taklif_yubor orqali yuboriladi).

    O'quvchi allaqachon javob bergan takliflar muddati o'tsa ham bekor
    qilinmaydi — ular navbatni yo'qotmaydi. Shuning uchun javob berilmagan
    (bo'sh yoki NULL) takliflargina qaraymiz.
    """
    muddati_otganlar = (
        Navbat.objects.select_related("kitob", "ajratilgan_nusxa")
        .filter(holati="taklif_qilindi", taklif_muddati__lt=now())
        .filter(Q(javob="") | Q(javob__isnull=True))
    )
    soni = 0
    for navbat in muddati_otganlar:
        try:
            taklifni_bekor_qil_va_keyingisiga_ut(navbat, "muddat_otdi")
        except Exception:
            # Bitta taklifni ko'rib chiqishdagi xato qolganlarini to'xtatmasin:
            # andoqsa bitta muammo bo'lgan taklif keyingi 10 daqiqada
            # qayta urinishni butunlay to'xtab qo'yadi.
            continue
        soni += 1
    return f"{soni} ta muddati o'tgan taklif bekor qilindi"
