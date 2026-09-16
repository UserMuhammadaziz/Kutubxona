from datetime import timedelta

from django.db import transaction
from django.utils.timezone import now

from nusxa.models import Nusxa
from .models import Navbat


def _botga_xabar_yubor(navbat):
    """Bot API'ga xabar yuborish shu yerda amalga oshiriladi (masalan
    requests.post yoki alohida bot-client moduli orqali). Hozircha stub."""
    pass


@transaction.atomic
def taklif_yubor(kitob_id, nusxa):
    """Navbatdagi eng eski odamga (navbat_sanasi bo'yicha birinchi) shu
    nusxani taklif qiladi. Navbat bo'sh bo'lsa hech narsa qilmay False
    qaytaradi."""
    navbat = (
        Navbat.objects.select_for_update()
        .filter(kitob_id=kitob_id, holati="kutmoqda")
        .order_by("navbat_sanasi")
        .first()
    )
    if not navbat:
        return False

    navbat.holati = "taklif_qilindi"
    navbat.ajratilgan_nusxa = nusxa
    navbat.taklif_vaqti = now()
    navbat.taklif_muddati = now() + timedelta(hours=24)
    navbat.save()

    nusxa.holati = "band"
    nusxa.save(update_fields=["holati"])

    transaction.on_commit(lambda: _botga_xabar_yubor(navbat))
    return True


def keyingi_navbatga_taklif_yubor(nusxa_id):
    """Kitob qaytarilgach chaqiriladi: nusxa hali 'mavjud' bo'lsa, shu
    kitobning navbatidagi birinchi odamga taklif yuboradi."""
    nusxa = Nusxa.objects.select_for_update().get(pk=nusxa_id)
    if nusxa.holati != "mavjud":
        return False
    return taklif_yubor(nusxa.kitob_id, nusxa)


@transaction.atomic
def taklifni_bekor_qil_va_keyingisiga_ut(navbat, sabab):
    """Taklifni bekor qiladi (o'quvchi rad etdi yoki 24 soat o'tdi) va
    nusxani darhol navbatdagi keyingi odamga taklif qiladi."""
    navbat = Navbat.objects.select_for_update().get(pk=navbat.pk)
    if navbat.holati != "taklif_qilindi":
        return

    navbat.holati = "bekor"
    navbat.bekor_sababi = sabab
    navbat.javob_vaqti = now()
    navbat.save()

    nusxa = navbat.ajratilgan_nusxa
    if nusxa:
        nusxa.holati = "mavjud"
        nusxa.save(update_fields=["holati"])
        taklif_yubor(navbat.kitob_id, nusxa)
