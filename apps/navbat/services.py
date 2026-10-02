from datetime import timedelta
from typing import NamedTuple

from django.conf import settings
from django.db import transaction
from django.utils.timezone import now

from config.telegram import telegram_escape, telegram_xabar_yubor
from nusxa.models import Nusxa
from .models import Navbat


class NavbatNatija(NamedTuple):
    """`navbatga_qosh` qaytargan ma'lumot: navbat yozuvi, o'rin raqami va
    yangi yozuv yaratilgani (`yangi=False` — o'quvchi allaqachon shu kitob
    navbatida edi)."""

    navbat: Navbat
    orin: int
    yangi: bool


def navbat_oringi(navbat):
    """Navbatdagi o'rin raqami: o'zidan olda nechta odam turgani."""
    return (
        Navbat.objects.filter(
            kitob=navbat.kitob,
            holati="kutmoqda",
            navbat_sanasi__lte=navbat.navbat_sanasi,
        ).count()
    )


@transaction.atomic
def navbatga_qosh(kitob, oquvchi):
    """O'quvchini kitob navbatiga qo'shadi. Agar o'quvchi allaqachon shu
    kitobning faol navbatida bo'lsa, yangi yozuv yaratilmaydi — mavjud
    navbat qaytariladi (unique_active_queue constraint'i buzilmasligi uchun)."""
    mavjud = (
        Navbat.objects.select_for_update()
        .filter(kitob=kitob, oquvchi=oquvchi, holati__in=["kutmoqda", "taklif_qilindi"])
        .first()
    )
    if mavjud:
        return NavbatNatija(navbat=mavjud, orin=navbat_oringi(mavjud), yangi=False)

    navbat = Navbat.objects.create(kitob=kitob, oquvchi=oquvchi)
    return NavbatNatija(navbat=navbat, orin=navbat_oringi(navbat), yangi=True)


def taklif_xabari_matni(navbat):
    """O'quvchiga yuboriladigan taklif xabarining matni (HTML parse_mode)."""
    muddat = navbat.taklif_muddati.strftime("%d.%m.%Y %H:%M")
    nomi = telegram_escape(navbat.kitob.nomi)
    muallif = telegram_escape(navbat.kitob.muallif)
    return (
        "🔔 <b>Navbatingiz yaqinlashdi!</b>\n\n"
        f"📖 <b>{nomi}</b>\n"
        f"✍️ {muallif}\n\n"
        f"Sizga ushbu kitob ajratildi. Kutubxonachiga murojaat qilib, "
        f"kitobni {muddat} dan oldin olib ketishingiz kerak.\n\n"
        "⏳ Kutubxonachining ish vaqti tugagach, kitob keyingi navbatdagiga "
        "o'tkaziladi."
    )


def _botga_xabar_yubor(navbat_id):
    """Taklif xabarini o'quvchining Telegram hisobiga yuboradi.

    Aniq bir marta yuborilishini kafolatlaydi: `taklif_xabari_yuborilgan`
    bayrogi taklif yuborilgan paytning o'zida (tranzaksiya ichida) True
    qilinadi, shuning uchun on_commit ishlayotgan bo'lishiga qaramay
    xabar ikkinchi marta yuborilmaydi.
    """
    navbat = (
        Navbat.objects.select_related("kitob", "oquvchi", "ajratilgan_nusxa")
        .filter(pk=navbat_id, taklif_xabari_yuborilgan=True)
        .first()
    )
    if not navbat:
        return False
    if not navbat.oquvchi.telegram_id:
        return False
    if not telegram_xabar_yubor(navbat.oquvchi.telegram_id, taklif_xabari_matni(navbat)):
        return False

    Navbat.objects.filter(pk=navbat.pk).update(taklif_xabari_yuborilgan=False)
    return True


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

    taklif_vaqti = now()
    navbat.holati = "taklif_qilindi"
    navbat.ajratilgan_nusxa = nusxa
    navbat.javob = ""
    navbat.taklif_vaqti = taklif_vaqti
    navbat.taklif_muddati = taklif_vaqti + timedelta(hours=settings.TAKLIF_SOAT)
    navbat.taklif_xabari_yuborilgan = True
    navbat.save(
        update_fields=[
            "holati",
            "ajratilgan_nusxa",
            "javob",
            "taklif_vaqti",
            "taklif_muddati",
            "taklif_xabari_yuborilgan",
        ]
    )

    nusxa.holati = "band"
    nusxa.save(update_fields=["holati"])

    transaction.on_commit(lambda: _botga_xabar_yubor(navbat.pk))
    return True


@transaction.atomic
def keyingi_navbatga_taklif_yubor(nusxa_id):
    """Kitob qaytarilgach chaqiriladi: nusxa hali 'mavjud' bo'lsa, shu
    kitobning navbatidagi birinchi odamga taklif yuboradi.

    `select_for_update` faqat tranzaksiya ichida ishlaydi, shuning uchun
    o'z ichiga atomik blok oladi — bu funksiya tranzaksiya tashqarisidan
    (masalan, Celery vazifasi orqali) chaqirilganda ham xato bermaydi.
    """
    nusxa = Nusxa.objects.select_for_update().get(pk=nusxa_id)
    if nusxa.holati != "mavjud":
        return False
    return taklif_yubor(nusxa.kitob_id, nusxa)


@transaction.atomic
def taklifni_bekor_qil_va_keyingisiga_ut(navbat, sabab, oquvchi_rozi=False):
    """Taklifni bekor qiladi (o'quvchi rad etdi yoki taklif muddati o'tdi) va
    nusxani darhol navbatdagi keyingi odamga taklif qiladi.

    O'quvchi allaqachon "olaman" deb javob bergan bo'lsa, taklif muddati
    o'tganiga qaramay bekor qilinmaydi — navbat kitob berilishini kutmoqda
    qoladi (berish/services.py berilganda yopadi). `oquvchi_rozi=True`
    berilsa (o'quvchi navbatdan chiqayotgan bo'lsa) bu himoya o'chadi."""
    navbat = Navbat.objects.select_for_update().get(pk=navbat.pk)
    if navbat.holati != "taklif_qilindi":
        return
    if navbat.javob == "olaman" and not oquvchi_rozi:
        return

    navbat.holati = "bekor"
    navbat.bekor_sababi = sabab
    navbat.javob_vaqti = now()
    navbat.taklif_xabari_yuborilgan = False
    navbat.save(update_fields=["holati", "bekor_sababi", "javob_vaqti", "taklif_xabari_yuborilgan"])

    nusxa = navbat.ajratilgan_nusxa
    if nusxa:
        nusxa.holati = "mavjud"
        nusxa.save(update_fields=["holati"])
        taklif_yubor(navbat.kitob_id, nusxa)
