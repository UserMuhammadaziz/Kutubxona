from celery import shared_task
from django.utils.timezone import now

from .models import Navbat
from .services import taklifni_bekor_qil_va_keyingisiga_ut


@shared_task
def takliflarni_tekshir():
    """
    Har 10 daqiqada ishlaydi. 24 soatlik javob muddati o'tib ketgan
    takliflarni bekor qiladi (bekor_sababi='muddat_otdi'), o'quvchiga
    xabar yuboradi va nusxani navbatdagi keyingi odamga taklif qiladi.
    """
    muddati_otganlar = Navbat.objects.filter(
        holati="taklif_qilindi",
        taklif_muddati__lt=now(),
    )
    soni = 0
    for navbat in muddati_otganlar:
        taklifni_bekor_qil_va_keyingisiga_ut(navbat, "muddat_otdi")
        soni += 1
    return f"{soni} ta muddati o'tgan taklif bekor qilindi"
