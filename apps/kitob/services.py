"""Kitob holatini nusxalar asosida avtomatik yangilash.

Kitob berilganda faqat `Nusxa.holati` o'zgaradi, lekin `Kitob.holati`
butunlay o'zgarishsiz qolardi — shuning uchun kitob ro'yxatida
«Mavjud» deb ko'rinib turar edi, garchi aslida nusxalari yo'q edi.

Bu modul kitob holatini nusxalar holatidan kelib chiqib hisoblaydi:

  * kamida bitta `mavjud` nusxa bor  -> «Mavjud»
  * `mavjud` nusxa yo'q, lekin `berilgan` nusxa bor -> «Berilgan»
  * nusxa umuman yo'q va kitob «asli» holda berilgan bo'lsa -> «Berilgan»
  * aks holda -> «Mavjud» (nusxa yo'q — aslida berish mumkin)

Muhim: «Yo'qolgan» — bu qo'lda belgilanadigan doimiy holat, shuning uchun
avtomatik yangilash uni hech qachon tegmaydi.
"""
from kitob.models import BandQilish, Kitob
from nusxa.models import Nusxa

from django.conf import settings
from django.db import transaction
from django.utils.timezone import now as django_now

from config.telegram import telegram_escape, telegram_xabar_yubor


def _faol_asli_berish_bormi(kitob_id):
    """Nusxasi yo'q kitob «asli» holda berilgan va hali qaytarilmaganmi?
    (import siklik bog'lanishdan qat'iy nazar, shu yerda qilinadi.)"""
    from berish.models import Berish

    return Berish.objects.filter(
        kitob_id=kitob_id, nusxa__isnull=True, qaytarilgan_sana__isnull=True
    ).exists()


def kitob_holatini_yenila(kitob_id):
    """`Kitob.holatini` nusxalar holatiga qarab yangilaydi va yangilangan
    qiymatni qaytaradi (o'zgarmagan bo'lsa ham `None` emas, joriy qiymat)."""
    nusxalar = Nusxa.objects.filter(kitob_id=kitob_id)

    mavjud_bormi = nusxalar.filter(holati="mavjud").exists()
    berilgan_bormi = nusxalar.filter(holati="berilgan").exists()
    # Nusxasi yo'q kitob faqat «asli» holda berilishi mumkin — bunda
    # ro'yxatda «Berilgan» deb ko'rinishi kerak.
    aslida_berilgan_bormi = not nusxalar.exists() and _faol_asli_berish_bormi(kitob_id)

    if mavjud_bormi:
        yangi = "mavjud"
    elif berilgan_bormi or aslida_berilgan_bormi:
        yangi = "berilgan"
    else:
        yangi = "mavjud"

    kitob = Kitob.objects.get(pk=kitob_id)
    if kitob.holati == "yoqolgan" or kitob.holati == yangi:
        # «Yo'qolgan» qo'lda belgilangan holat — uni saqlaymiz.
        return kitob.holati

    kitob.holati = yangi
    kitob.save(update_fields=["holati"])
    return yangi


# ---------------------------------------------------------------- band qilish
def faol_band_bormi(kitob_id):
    """Bu kitob uchun tasdiqlash kutilayotgan band so'rovi bormi?

    `berish/services.py` shu yordamchiga qarab kitob berilishini
    to'xtatadi: band qilingan kitob faqat kutubxonachi tasdiqlagandan
    keyin berilishi kerak."""
    return BandQilish.objects.filter(kitob_id=kitob_id, holati="kutmoqda").exists()


def faol_bandni_top(kitob_id):
    """Tasdiqlash kutilayotgan band so'rovi (yo'q bo'lsa `None`)."""
    return BandQilish.objects.filter(
        kitob_id=kitob_id, holati="kutmoqda"
    ).select_related("oquvchi", "kitob").first()


def _band_xato(kod, detail, **qoshimcha):
    from rest_framework.exceptions import ValidationError

    raise ValidationError({"error": kod, "detail": detail, **qoshimcha})


def band_qilish(kitob, oquvchi, izoh=""):
    """Kitobni band qilish so'rovini yaratadi.

    Band qilingandan keyin kitob hech kimga berilmaydi: berish
    `berish/services.py::kitob_ber` ichida `faol_band_bormi()` orqali
    bloklanadi. Kitobni faqat kutubxonachi yoki administrator tasdiqlab,
    so'rov yaratuvchiga berish yozuvini ochishi mumkin (`tasdiqla()`).

    Idempotent: aynan shu o'quvchi shu kitob uchun allaqachon so'rov
    yuborgan bo'lsa, mavjud so'rov qaytariladi (ikki marta band qilinmaydi).
    """
    from berish.models import Berish

    if not oquvchi.faol:
        _band_xato("oquvchi_bloklangan", "O'quvchi bloklangan")

    mavjud = BandQilish.objects.filter(
        kitob=kitob, oquvchi=oquvchi, holati="kutmoqda"
    ).first()
    if mavjud:
        return mavjud, False

    boshqa = faol_bandni_top(kitob.pk)
    if boshqa:
        _band_xato(
            "allaqachon_band_qilingan",
            "Bu kitob boshqa o'quvchi uchun band qilingan",
            band_id=boshqa.pk,
        )

    if Berish.objects.filter(
        kitob_id=kitob.pk, oquvchi=oquvchi, qaytarilgan_sana__isnull=True
    ).exists():
        _band_xato("allaqachon_berilgan", "Bu kitob allaqachon olganizda bor")

    band = BandQilish.objects.create(kitob=kitob, oquvchi=oquvchi, izoh=izoh or "")
    _xodimlarga_xabar_yubor(band)
    return band, True


def _xodimlarga_xabar_yubor(band):
    """Yangi band so'rovi haqida kutubxonachi/administratorlarga xabar.

    Xodimlar `.env` dagi `BOT_ADMIN_CHAT_IDS` ro'yxatiga kirgan Telegram
    hisoblar; ro'yxat bo'sh bo'lsa xabar yuborilmaydi (xato ham chiqmaydi) —
    tasdiqlash web-panel orqali ham mumkin.
    """
    import os

    from config.telegram import telegram_escape, telegram_xabar_yubor

    raw = os.environ.get("BOT_ADMIN_CHAT_IDS", "")
    chat_idlar = [
        int(q.strip())
        for q in raw.split(",")
        if q.strip().lstrip("-").isdigit()
    ]
    if not chat_idlar:
        return

    rol = "o'qituvchi" if band.oquvchi.rol == "oqituvchi" else "o'quvchi"
    qator = f"🔒 Yangi band so'rovi: {telegram_escape(band.kitob.nomi)}"
    if band.izoh:
        qator += f"\n📝 {telegram_escape(band.izoh)}"
    matn = (
        f"{qator}\n"
        f"So'raydi: {telegram_escape(band.oquvchi.fish)} ({rol})\n"
        f"Tasdiqlash uchun botda /bandlar buyrug'ini bosing."
    )
    for chat_id in chat_idlar:
        telegram_xabar_yubor(chat_id, matn)


def band_qilishni_bekor_qil(band, oquvchi):
    """O'quvchi kutayotgan band so'rovini bekor qiladi."""
    if band.oquvchi_id != oquvchi.pk:
        _band_xato("ruxsat_yuq", "Bu so'rov sizniki emas")
    if band.holati != "kutmoqda":
        _band_xato("so_rov_yopilgan", "Bu so'rov allaqachon yopilgan")
    band.holati = "bekor_qilindi"
    band.tasdiqlash_sanasi = django_now()
    band.save(update_fields=["holati", "tasdiqlash_sanasi"])
    return band


def band_qilishni_rad_et(band, xodim, izoh=""):
    """Kutubxonachi/administrator band so'rovini rad etadi."""
    _band_holatini_tekshir(band)
    band.holati = "rad_etildi"
    band.tasdiqlovchi = xodim
    band.tasdiqlash_izohi = izoh or ""
    band.tasdiqlash_sanasi = django_now()
    band.save(
        update_fields=["holati", "tasdiqlovchi", "tasdiqlash_izohi", "tasdiqlash_sanasi"]
    )
    transaction.on_commit(lambda: _band_rad_etildi_xabarini_yubor(band))
    return band


def _band_holatini_tekshir(band):
    if band.holati != "kutmoqda":
        _band_xato(
            "so_rov_yopilgan",
            "Bu so'rov allaqachon yopilgan",
            holati=band.holati,
        )


def band_qilishni_tasdiqla(band, xodim, izoh=""):
    """Band so'rovini tasdiqlaydi va kitobni so'rov qilgan o'quvchiga beradi.

    Muhim: tasdiqlash — berishning yagona yo'li. Shu sababli berish
    `band_tasdiqlandi=True` bilan chaqiriladi, aks holda band himoyasi
    (boshqa hech kimga berilmasligi) tasdiqlashni o'zi bloklab qo'yardi.
    """
    from berish.services import kitob_ber_by_kitob

    with transaction.atomic():
        band = (
            BandQilish.objects.select_for_update()
            .select_related("kitob", "oquvchi")
            .get(pk=band.pk)
        )
        _band_holatini_tekshir(band)

        nusxa_mavjud = Nusxa.objects.filter(kitob_id=band.kitob_id, holati="mavjud").exists()
        if not nusxa_mavjud and Nusxa.objects.filter(kitob_id=band.kitob_id).exists():
            _band_xato(
                "berish_mumkin_emas",
                "Bu kitobning barcha nusxalari hozir berilgan — berish uchun "
                "avval nusxa bo'shatish kerak",
            )

        berish = kitob_ber_by_kitob(
            band.kitob, band.oquvchi, xodim, band_tasdiqlandi=True
        )
        band.holati = "tasdiqlandi"
        band.tasdiqlovchi = xodim
        band.tasdiqlash_izohi = izoh or ""
        band.tasdiqlash_sanasi = django_now()
        band.berish = berish
        band.save(
            update_fields=[
                "holati", "tasdiqlovchi", "tasdiqlash_izohi", "tasdiqlash_sanasi", "berish",
            ]
        )
    transaction.on_commit(lambda: _band_tasdiqlandi_xabarini_yubor(band))
    return band, berish


# ---------------------------------------------------------------------------
# Band so'rovi natijalarini o'quvchiga yetkazish
#
# Bot xabar qiladi: «Tasdiqlanganligi xabar qilinadi» — shu vaat xabar
# yuborilishi SHART, aks holda yozuv yolg'on bo'ladi. Xabar tranzaksiya
# commit bo'lgandan keyin yuboriladi (rollback bo'lsa yuborilmaydi).
# ---------------------------------------------------------------------------


def _band_tasdiqlandi_xabarini_yubor(band):
    """Band tasdiqlandi: o'quvchiga xabar + qaytarish muddati.

    `band.berish` band bilan bir vaqtda saqlanadi (yuqorida `save()`),
    shuning uchun `on_commit` ichida mavjud bo'ladi. Xabar yuborilmasa ham
    tasdiqlash amalga oshgan bo'ladi."""
    if not band.oquvchi.telegram_id:
        return
    berish = band.berish
    matn = (
        "◈ <b>KUTUBXONA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Band qilish tasdiqlandi</b>\n\n"
        f"Kitob: <b>{telegram_escape(band.kitob.nomi)}</b>\n"
    )
    if berish is not None:
        matn += (
            f"Berilgan sana: {berish.berilgan_sana}\n"
            f"Qaytarish muddati: <b>{berish.qaytarish_muddati}</b>\n\n"
            f"Iltimos, kitobni {settings.MUDDAT_KUN} kun ichida qaytaring."
        )
    else:  # pragma: no cover — himoya; berish har doim yaratiladi
        matn += "Kitob sizga berishga tayyor. Qaytarish muddati uchun botga yozing."
    telegram_xabar_yubor(band.oquvchi.telegram_id, matn)


def _band_rad_etildi_xabarini_yubor(band):
    """Band rad etildi: o'quvchiga xabar (+ kutubxonachining izohi, bo'lsa)."""
    if not band.oquvchi.telegram_id:
        return
    matn = (
        "◈ <b>KUTUBXONA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Band qilish rad etildi</b>\n\n"
        f"Kitob: <b>{telegram_escape(band.kitob.nomi)}</b>\n"
    )
    if band.tasdiqlash_izohi:
        matn += f"\nSabab: {telegram_escape(band.tasdiqlash_izohi)}"
    matn += "\n\nBoshqa kitob band qilmoqchi bo'lsangiz, qayta urinib ko'ring."
    telegram_xabar_yubor(band.oquvchi.telegram_id, matn)