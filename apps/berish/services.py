from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from config.telegram import telegram_escape, telegram_xabar_yubor
from jarima.models import Jarima
from jarima.services import jarimani_hisobla
from kitob.services import kitob_holatini_yenila
from navbat.models import Navbat
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

    # Kitobning o'z holati ham nusxalardan kelib chiqib yangilanadi —
    # aks holda kitob ro'yxatida «Mavjud» deb ko'rinib turar edi.
    kitob_holatini_yenila(nusxa.kitob_id)

    berish = Berish.objects.create(
        nusxa=nusxa,
        oquvchi=oquvchi,
        bergan_xodim=xodim,
        qaytarish_muddati=now().date() + timedelta(days=settings.MUDDAT_KUN),
        holati="faol",
    )

    # Foydalanuvchi tayinlagan navbat (band) endi berilganligi tasdiqlanadi.
    # taklif_xabari_yuborilgan=False: o'quvchi allaqachon "Kitob berildi"
    # xabarini oladi, taklif xabari esa kerak emas (takroriy xabar bo'lmasin).
    Navbat.objects.filter(
        kitob=nusxa.kitob_id,
        oquvchi=oquvchi,
        holati__in=["kutmoqda", "taklif_qilindi"],
    ).update(
        holati="yakunlandi",
        javob_vaqti=now(),
        taklif_xabari_yuborilgan=False,
    )

    # Kitob olgan kundan boshlab qaytarish muddati (14 kun) boshlanadi.
    transaction.on_commit(lambda: _kitob_berildi_xabarini_yubor(berish))

    return berish


def _kitob_berildi_xabarini_yubor(berish):
    """Berish tranzaksiyasi commit bo'lgach, o'quvchiga Telegram xabar yuboradi:
    «Kitob berildi» + qaytarish muddati + olgan kundan hisoblanadigan muddat."""
    oquvchi = berish.oquvchi
    if not oquvchi.telegram_id:
        return
    matn = (
        "📖 <b>Kitob berildi!</b>\n\n"
        f"Qabul qilgan kitobingiz: <b>{telegram_escape(berish.nusxa.kitob.nomi)}</b>\n"
        f"Inventar raqami: {berish.nusxa.inventar_raqami}\n"
        f"Berilgan sana: {berish.berilgan_sana}\n"
        f"Qaytarish muddati: <b>{berish.qaytarish_muddati}</b>\n\n"
        f"Sizda kitobni olgan kundan boshlab {settings.MUDDAT_KUN} kun muddat bor. "
        "Iltimos, vaqtida topshiring!"
    )
    telegram_xabar_yubor(oquvchi.telegram_id, matn)


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

    # Nusxa bo'shatildi — kitob holati ham qayta "Mavjud" ga qaytadi
    # (agar boshqa mavjud nusxa bo'lsa, allaqachon "Mavjud" bo'lib qoladi).
    kitob_holatini_yenila(nusxa.kitob_id)

    jarima = jarimani_hisobla(berish)
    taklif_ketdi = keyingi_navbatga_taklif_yubor(nusxa.id)

    return berish, jarima, taklif_ketdi
