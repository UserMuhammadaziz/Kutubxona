from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from berish.models import Berish
from config.telegram import telegram_escape, telegram_xabar_yubor
from organization.models import Organization
from oquvchi.models import Oquvchi

from .models import KitobXabari, OylikStatistika
from .services import botni_ol


def _qisqa_avail_nomi(kitob):
    jami = kitob.nusxalar.count()
    mavjud = kitob.nusxalar.filter(holati="mavjud").count()
    if not jami:
        return "Nusxalar yo'q — berilishi mumkin"
    if mavjud:
        return f"Mavjud: {mavjud} / Jami: {jami} — hozir olish mumkin"
    return f"Mavjud: 0 / Jami: {jami} — hozir barcha berilgan (navbatga yozilish mumkin)"


@shared_task
def yangi_kitob_xabari_yubor(kitob_id):
    from kitob.models import Kitob

    kitob = Kitob.objects.select_related("organization").filter(pk=kitob_id).first()
    if not kitob or not kitob.organization:
        return "skip"
    if not kitob.organization.kitob_xabarlari_yoqilgan:
        return "disabled"
    xabar, _ = KitobXabari.objects.get_or_create(
        organization=kitob.organization, kitob=kitob, tur="yangi"
    )
    if xabar.yuborildi:
        return "already"
    bot = botni_ol(kitob.organization)
    if not bot or bot.holati != "ulangan":
        return "no_bot"

    qisqa = _qisqa_avail_nomi(kitob)
    qisqacha_holat = (
        "Mavjud" if kitob.nusxalar.filter(holati="mavjud").count() else "Hozirda yo'q"
    )
    batafsil = (
        f"📚 <b>YANGI KITOB QO'SHILDI</b>\n\n"
        f"Nom: <b>{telegram_escape(kitob.nomi)}</b>\n"
        f"Muallif: {telegram_escape(kitob.muallif)}\n"
        f"Janr: {telegram_escape(kitob.get_janr_display())}\n"
        f"Nashr yili: {kitob.nashr_yili}\n"
        f"Til: {telegram_escape(kitob.get_til_display()) if kitob.til else '-'}\n"
        f"ISBN: {telegram_escape(kitob.isbn) if kitob.isbn else '-'}\n\n"
        f"<b>Holati (batafsil):</b> {telegram_escape(qisqa)}\n"
        f"<b>Qisqacha:</b> {qisqacha_holat}\n"
    )
    if kitob.tavsif:
        batafsil += f"\nTavsif: {telegram_escape(kitob.tavsif[:200])}"

    yuborilgan = 0
    qabul = (
        Oquvchi.objects.filter(
            organization=kitob.organization, faol=True, telegram_id__isnull=False
        )
        .values_list("telegram_id", flat=True)
        .distinct()
    )
    for tid in qabul:
        if telegram_xabar_yubor(
            tid,
            batafsil,
            organization=kitob.organization,
            bot=bot,
        ):
            yuborilgan += 1
    xabar.yuborildi = True
    xabar.yuborilgan_soni = yuborilgan
    xabar.yuborilgan_sana = timezone.now()
    xabar.save(update_fields=["yuborildi", "yuborilgan_soni", "yuborilgan_sana"])
    return f"{yuborilgan}"


OYLAR = [
    "yanvar", "fevral", "mart", "aprel", "may", "iyun",
    "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr",
]


def _oylik_matn(oquvchi, oy_boshi, berishlar, kechikkanlar) -> str:
    """Bitta foydalanuvchi uchun shaxsiy oylik statistika matni."""
    oy_nomi = f"{oy_boshi.year}-yil {OYLAR[oy_boshi.month - 1]}-oyi"
    qatorlar = [
        f"📊 <b>Oylik statistika</b> — {oy_nomi}",
        "",
        f"👤 Ism familiya: <b>{telegram_escape(oquvchi.fish)}</b>",
    ]
    if oquvchi.rol == "oqituvchi" and oquvchi.kasb:
        qatorlar.append(f"📚 Fan: {telegram_escape(oquvchi.kasb)}")
    elif oquvchi.sinf:
        qatorlar.append(f"🎓 Sinf: {telegram_escape(oquvchi.sinf)}")

    qatorlar.append("")
    if berishlar:
        qatorlar.append(
            f"📖 O'tgan oyda o'qigan kitoblaringiz: <b>{len(berishlar)}</b>"
        )
        for berish in berishlar[:15]:
            qatorlar.append(f"• {telegram_escape(berish.kitob.nomi)}")
        if len(berishlar) > 15:
            qatorlar.append(f"… yana {len(berishlar) - 15} ta")
    else:
        qatorlar.append("📖 O'tgan oyda kitob olinmadi.")

    qatorlar.append("")
    if kechikkanlar:
        qatorlar.append(
            f"⏰ Muddatdan kech bergan kitoblaringiz: <b>{len(kechikkanlar)}</b>"
        )
        for berish in kechikkanlar[:10]:
            if berish.qaytarilgan_sana:
                kun = (berish.qaytarilgan_sana - berish.qaytarish_muddati).days
                izoh = f"{kun} kun kech qaytarildi"
            else:
                izoh = f"hali qaytarilmadi (muddati: {berish.qaytarish_muddati})"
            qatorlar.append(f"• {telegram_escape(berish.kitob.nomi)} — {izoh}")
    else:
        qatorlar.append("✅ Muddatdan kechikish kuzatilmadi.")

    qatorlar.extend(["", "Yaxshi o'qish tilaymiz! 📚"])
    return "\n".join(qatorlar)


@shared_task
def oylik_statistika_yubor():
    """Har oyning 1ida soat 08:00 da (Toshkent vaqti) ishlaydi.

    O'tgan oy bo'yicha har bir faol o'quvchi/o'qituvchiga shaxsiy statistika
    yuboriladi: ism-familiya, o'qigan kitoblari va muddatdan kech berganligi.
    """
    bugun = timezone.localdate()
    oy_boshi = bugun.replace(day=1)
    oldingi_oy_oxiri = oy_boshi - timedelta(days=1)
    oldingi_oy_boshi = oldingi_oy_oxiri.replace(day=1)

    oquvchilar = Oquvchi.objects.filter(
        faol=True, telegram_id__isnull=False
    ).select_related("organization").order_by("pk")

    yuborilgan = 0
    otkazilgan = 0
    for oquvchi in oquvchilar.iterator():
        # Muvaffaqiyatli yuborilganlar qayta yuborilmaydi; yuborish xato
        # berganlar keyingi chaqiruvda yana urinib ko'radi.
        if OylikStatistika.objects.filter(
            oquvchi=oquvchi, oy=oldingi_oy_boshi, yuborildi=True
        ).exists():
            continue

        berishlar = list(
            Berish.objects.filter(
                organization=oquvchi.organization,
                oquvchi=oquvchi,
                berilgan_sana__gte=oldingi_oy_boshi,
                berilgan_sana__lte=oldingi_oy_oxiri,
            ).select_related("kitob")
        )
        kechikkanlar = [
            b for b in berishlar
            if (b.qaytarilgan_sana and b.qaytarilgan_sana > b.qaytarish_muddati)
            or (b.qaytarilgan_sana is None and b.qaytarish_muddati < bugun)
        ]
        matn = _oylik_matn(oquvchi, oldingi_oy_boshi, berishlar, kechikkanlar)

        muvaffaqiyatli = telegram_xabar_yubor(
            oquvchi.telegram_id, matn, organization=oquvchi.organization
        )
        qayd, _ = OylikStatistika.objects.get_or_create(
            organization=oquvchi.organization,
            oquvchi=oquvchi,
            oy=oldingi_oy_boshi,
        )
        qayd.yuborildi = bool(muvaffaqiyatli)
        qayd.xato = "" if muvaffaqiyatli else "telegramga yuborib bo'lmadi"
        if muvaffaqiyatli:
            qayd.yuborilgan_sana = timezone.now()
            yuborilgan += 1
        else:
            otkazilgan += 1
        qayd.save(update_fields=["yuborildi", "xato", "yuborilgan_sana"])

    return f"{yuborilgan} ta statistika yuborildi, {otkazilgan} ta yuborilmadi"
