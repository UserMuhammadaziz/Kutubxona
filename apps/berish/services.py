from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from jarima.models import Jarima
from jarima.services import jarimani_hisobla
from navbat.services import keyingi_navbatga_taklif_yubor
from nusxa.models import Nusxa
from .models import Berish


def _xato(kod, detail):
    raise ValidationError({"error": kod, "detail": detail})


@transaction.atomic
def kitob_ber(nusxa, oquvchi, xodim):
    """Kitob berish: barcha biznes cheklovlarni tekshiradi, so'ng nusxa
    holatini va Berish yozuvini bitta tranzaksiyada o'zgartiradi."""
    if not oquvchi.faol:
        _xato("oquvchi_bloklangan", "O'quvchi bloklangan")

    faol_soni = Berish.objects.filter(oquvchi=oquvchi, qaytarilgan_sana__isnull=True).count()
    if faol_soni >= settings.LIMIT_KITOB:
        _xato("limit_oshdi", f"O'quvchida allaqachon {settings.LIMIT_KITOB} ta kitob bor")

    if Jarima.objects.filter(berish__oquvchi=oquvchi, tolandimi=False).exists():
        _xato("tolanmagan_jarima", "O'quvchida to'lanmagan jarima bor")

    nusxa = Nusxa.objects.select_for_update().get(pk=nusxa.pk)
    if nusxa.holati != "mavjud":
        _xato("nusxa_band", "Bu nusxa hozir mavjud emas")

    nusxa.holati = "berilgan"
    nusxa.save(update_fields=["holati"])

    berish = Berish.objects.create(
        nusxa=nusxa,
        oquvchi=oquvchi,
        bergan_xodim=xodim,
        qaytarish_muddati=now().date() + timedelta(days=settings.MUDDAT_KUN),
        holati="faol",
    )
    return berish


@transaction.atomic
def kitob_qaytar(berish, xodim):
    """Kitobni qaytarib olish: avval nusxani bo'shatadi, jarimani hisoblaydi
    (bor bo'lsa), so'ng navbatdagi keyingi odamga taklif yuboradi (bo'lsa)."""
    berish = Berish.objects.select_for_update().get(pk=berish.pk)
    berish.qaytarilgan_sana = now().date()
    berish.olgan_xodim = xodim
    berish.holati = "qaytarilgan"
    berish.save()

    nusxa = Nusxa.objects.select_for_update().get(pk=berish.nusxa_id)
    nusxa.holati = "mavjud"
    nusxa.save(update_fields=["holati"])

    jarima = jarimani_hisobla(berish)
    taklif_ketdi = keyingi_navbatga_taklif_yubor(nusxa.id)

    return berish, jarima, taklif_ketdi
