"""Kutubxona botining webhook handleri.

Har bir so'rov faqat `bot.organization` doirasida ishlaydi. Foydalanuvchi
yuborgan ID'lar (kitob, band, navbat) har doim shu kutubxona bo'yicha
qayta tekshiriladi — boshqa kutubxona obyektiga murojaat qilib bo'lmaydi.
"""

import re

from django.db.models import Count, Q
from django.utils import timezone

from berish.models import Berish
from config.telegram import telegram_escape
from jarima.models import Jarima
from kitob.models import BandQilish, Kitob
from navbat.models import Navbat
from organization.models import Membership
from oquvchi.models import Ariza, Oquvchi

from .client import answer_callback_query
from .models import TelegramSession
from .services import xabar_yubor

TELEFON_RE = re.compile(r"^\+998\d{9}$")

READER_MENU = {
    "keyboard": [
        [{"text": "🔎 Kitob qidirish"}, {"text": "📚 Kategoriyalar"}],
        [{"text": "📖 Mening kitoblarim"}, {"text": "⏳ Navbatlarim"}],
        [{"text": "💰 Jarimalarim"}, {"text": "🔒 Band qilganlarim"}],
        [{"text": "ℹ️ Yordam"}],
    ],
    "resize_keyboard": True,
}

STAFF_MENU = {
    "keyboard": [
        [{"text": "🔔 Band so'rovlar"}, {"text": "↩️ Qaytarish"}],
        [{"text": "📊 Statistika"}, {"text": "ℹ️ Yordam"}],
    ],
    "resize_keyboard": True,
}


def _inline(rows):
    return {"inline_keyboard": rows}


def _send(bot, chat_id, matn, reply_markup=None):
    return xabar_yubor(bot, chat_id, matn, reply_markup=reply_markup)


def _reader(bot, telegram_id):
    return Oquvchi.objects.filter(
        organization=bot.organization, telegram_id=telegram_id, faol=True
    ).first()


def _staff(bot, telegram_id):
    return (
        Membership.objects.select_related("user")
        .filter(
            organization=bot.organization,
            telegram_id=telegram_id,
            faol=True,
            rol__in=["egasi", "administrator", "kutubxonachi"],
        )
        .first()
    )


def _session(bot, telegram_id):
    return TelegramSession.objects.filter(bot=bot, telegram_id=telegram_id).first()


def _set_session(bot, telegram_id, chat_id, step, data=None):
    TelegramSession.objects.update_or_create(
        bot=bot,
        telegram_id=telegram_id,
        defaults={"chat_id": chat_id, "step": step, "data": data or {}},
    )


def _clear_session(bot, telegram_id):
    TelegramSession.objects.filter(bot=bot, telegram_id=telegram_id).delete()


def _menu(bot, telegram_id):
    if _staff(bot, telegram_id):
        return STAFF_MENU
    return READER_MENU


def _start(bot, message):
    chat_id = message["chat"]["id"]
    telegram_id = message["from"]["id"]
    _clear_session(bot, telegram_id)
    oquvchi = _reader(bot, telegram_id)
    if oquvchi:
        _send(
            bot,
            chat_id,
            "◈ <b>KUTUBXONA</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Xush kelibsiz, <b>{telegram_escape(oquvchi.fish)}</b>!\n"
            "Kerakli bo'limni tanlang.",
            _menu(bot, telegram_id),
        )
        return
    xodim = _staff(bot, telegram_id)
    if xodim:
        _send(
            bot,
            chat_id,
            f"Salom, <b>{telegram_escape(xodim.user.full_name)}</b>!\n"
            "Kutubxonachi paneli tayyor.",
            STAFF_MENU,
        )
        return
    ariza = Ariza.objects.filter(
        organization=bot.organization, telegram_id=telegram_id
    ).first()
    if ariza and ariza.holati == "kutmoqda":
        _send(
            bot,
            chat_id,
            "Arizangiz ko'rib chiqilmoqda. Tasdiqlangach xabar beramiz.",
            {"remove_keyboard": True},
        )
        return
    _send(
        bot,
        chat_id,
        "◈ <b>KUTUBXONA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "A'zo bo'lish uchun rolingizni tanlang:",
        _inline(
            [
                [
                    {"text": "🎓 O'quvchi", "callback_data": "rol:oquvchi"},
                    {"text": "👨‍🏫 O'qituvchi", "callback_data": "rol:oqituvchi"},
                ]
            ]
        ),
    )


def _ariza_rol(bot, chat_id, telegram_id, rol):
    if rol not in ("oquvchi", "oqituvchi"):
        return
    if _reader(bot, telegram_id) or _staff(bot, telegram_id):
        _send(bot, chat_id, "Siz allaqachon ro'yxatdan o'tgansiz.", _menu(bot, telegram_id))
        return
    _set_session(bot, telegram_id, chat_id, "ariza_fish", {"rol": rol})
    _send(bot, chat_id, "Ism va familiyangizni kiriting:", {"remove_keyboard": True})


def _ariza_text(bot, message, sessiya):
    chat_id = message["chat"]["id"]
    telegram_id = message["from"]["id"]
    matn = (message.get("text") or "").strip()
    data = sessiya.data or {}
    step = sessiya.step
    if step == "ariza_fish":
        if len(matn) < 3:
            _send(bot, chat_id, "Ism-familiya juda qisqa. Qaytadan kiriting.")
            return
        data["fish"] = matn[:130]
        _set_session(bot, telegram_id, chat_id, "ariza_telefon", data)
        _send(bot, chat_id, "Telefon raqamingizni +998XXXXXXXXX formatida kiriting:")
        return
    if step == "ariza_telefon":
        if not TELEFON_RE.match(matn):
            _send(bot, chat_id, "Telefon +998123456789 formatida bo'lishi kerak.")
            return
        if Oquvchi.objects.filter(
            organization=bot.organization, telefon=matn
        ).exists():
            _send(bot, chat_id, "Bu telefon raqam bilan o'quvchi allaqachon ro'yxatda.")
            return
        data["telefon"] = matn
        if data.get("rol") == "oqituvchi":
            _set_session(bot, telegram_id, chat_id, "ariza_kasb", data)
            _send(bot, chat_id, "Qaysi fanni o'qitasiz? (masalan: Matematika)")
        else:
            _set_session(bot, telegram_id, chat_id, "ariza_sinf", data)
            _send(bot, chat_id, "Sinfingizni kiriting (masalan: 7-A):")
        return
    if step in ("ariza_sinf", "ariza_kasb"):
        if len(matn) < 1 or len(matn) > 60:
            _send(bot, chat_id, "Qiymat 1-60 belgi orasida bo'lishi kerak.")
            return
        rol = data.get("rol", "oquvchi")
        if rol == "oqituvchi":
            data["kasb"] = matn
        else:
            data["sinf"] = matn
        if Ariza.objects.filter(
            organization=bot.organization, telegram_id=telegram_id, holati="kutmoqda"
        ).exists():
            _send(bot, chat_id, "Arizangiz allaqachon ko'rib chiqilmoqda.")
            _clear_session(bot, telegram_id)
            return
        Ariza.objects.filter(
            organization=bot.organization, telegram_id=telegram_id
        ).exclude(holati="kutmoqda").delete()
        Ariza.objects.create(
            organization=bot.organization,
            telegram_id=telegram_id,
            fish=data["fish"],
            telefon=data["telefon"],
            rol=rol,
            sinf=data.get("sinf") if rol == "oquvchi" else None,
            kasb=data.get("kasb", "") if rol == "oqituvchi" else "",
        )
        _clear_session(bot, telegram_id)
        _send(
            bot,
            chat_id,
            "✅ Arizangiz qabul qilindi. Kutubxonachi tasdiqlagach xabar beramiz.",
            {"remove_keyboard": True},
        )
        return
    if step == "qidiruv":
        _clear_session(bot, telegram_id)
        _qidiruv(bot, chat_id, telegram_id, matn)
        return
    if step == "qaytarish":
        _clear_session(bot, telegram_id)
        _qaytarish(bot, chat_id, telegram_id, matn)
        return


def _qidiruv(bot, chat_id, telegram_id, q):
    oquvchi = _reader(bot, telegram_id)
    if not oquvchi:
        _send(bot, chat_id, "Avval /start orqali ro'yxatdan o'ting.")
        return
    if not q:
        _send(bot, chat_id, "Qidiruv so'zini kiriting.")
        return
    kitoblar = (
        Kitob.objects.filter(organization=bot.organization)
        .filter(Q(nomi__icontains=q) | Q(muallif__icontains=q) | Q(isbn__icontains=q))
        .annotate(
            mavjud_soni=Count("nusxalar", filter=Q(nusxalar__holati="mavjud")),
            jami_soni=Count("nusxalar"),
        )
        .order_by("nomi")[:10]
    )
    if not kitoblar:
        _send(bot, chat_id, "Hech narsa topilmadi. Boshqacha so'z bilan urinib ko'ring.")
        return
    rows = []
    for kitob in kitoblar:
        belgi = "🟢" if kitob.mavjud_soni else "🔴"
        rows.append(
            [
                {
                    "text": f"{belgi} {kitob.nomi[:45]}",
                    "callback_data": f"kitob:{kitob.pk}",
                }
            ]
        )
    _send(bot, chat_id, "Topilgan kitoblar:", _inline(rows))


def _kitob_karta(bot, chat_id, telegram_id, kitob_id, callback_id=None):
    kitob = Kitob.objects.filter(organization=bot.organization, pk=kitob_id).first()
    if not kitob:
        _send(bot, chat_id, "Kitob topilmadi.")
        return
    faol_berishlar = Berish.objects.filter(
        organization=bot.organization, kitob=kitob, qaytarilgan_sana__isnull=True
    ).select_related("oquvchi", "nusxa")
    mavjud = kitob.nusxalar.filter(holati="mavjud").count()
    jami = kitob.nusxalar.count()
    matn = (
        f"📖 <b>{telegram_escape(kitob.nomi)}</b>\n"
        f"✍️ {telegram_escape(kitob.muallif)}\n"
        f"🏷 {telegram_escape(kitob.get_janr_display())}\n"
        f"📅 {kitob.nashr_yili}"
        + (f" · {telegram_escape(kitob.nashriyot)}" if kitob.nashriyot else "")
        + "\n"
    )
    if kitob.isbn:
        matn += f"🔢 ISBN: {telegram_escape(kitob.isbn)}\n"
    matn += f"\n📦 Jami nusxa: <b>{jami}</b> · Mavjud: <b>{mavjud}</b>\n"
    if not jami:
        matn += "ℹ️ Nusxa yo'q — kitob «asli» holda beriladi.\n"
    elif mavjud:
        matn += "✅ Hozir mavjud, hech kimda emas.\n"
    else:
        matn += "⛔ Hozir barcha nusxalar berilgan.\n"
    if faol_berishlar.exists():
        matn += "\n<b>Hozir kimda:</b>\n"
        for berish in faol_berishlar[:5]:
            kim = berish.oquvchi
            sinf = kim.kasb if kim.rol == "oqituvchi" else kim.sinf
            matn += (
                f"• {telegram_escape(kim.fish)}"
                f"{f' ({telegram_escape(sinf)})' if sinf else ''} — "
                f"{berish.qaytarish_muddati}\n"
            )
    tugmalar = [
        [{"text": "🔒 Band qilish", "callback_data": f"band:{kitob.pk}"}],
    ]
    if not mavjud:
        tugmalar.append(
            [{"text": "⏳ Navbatga yozilish", "callback_data": f"navbat:{kitob.pk}"}]
        )
    _send(bot, chat_id, matn, _inline(tugmalar))
    if callback_id:
        try:
            answer_callback_query(bot.get_token(), callback_id)
        except Exception:
            pass


def _band_qilish(bot, chat_id, telegram_id, kitob_id):
    oquvchi = _reader(bot, telegram_id)
    if not oquvchi:
        _send(bot, chat_id, "Avval /start orqali ro'yxatdan o'ting.")
        return
    kitob = Kitob.objects.filter(organization=bot.organization, pk=kitob_id).first()
    if not kitob:
        _send(bot, chat_id, "Kitob topilmadi.")
        return
    from kitob.services import band_qilish

    try:
        band, yangi = band_qilish(kitob, oquvchi, "Telegram bot orqali")
    except Exception as xato:
        _send(bot, chat_id, f"Band qilish mumkin emas: {telegram_escape(xato)}")
        return
    if yangi:
        _send(
            bot,
            chat_id,
            f"🔒 <b>{telegram_escape(kitob.nomi)}</b> band qilindi.\n"
            "Kutubxonachi tasdiqlagach xabar beramiz.",
        )
    else:
        _send(bot, chat_id, "Bu kitob siz tomoningizdan allaqachon band qilingan.")


def _navbatga_qosh(bot, chat_id, telegram_id, kitob_id):
    oquvchi = _reader(bot, telegram_id)
    if not oquvchi:
        _send(bot, chat_id, "Avval /start orqali ro'yxatdan o'ting.")
        return
    kitob = Kitob.objects.filter(organization=bot.organization, pk=kitob_id).first()
    if not kitob:
        _send(bot, chat_id, "Kitob topilmadi.")
        return
    from navbat.services import navbatga_qosh

    natija = navbatga_qosh(kitob, oquvchi)
    _send(
        bot,
        chat_id,
        f"⏳ <b>{telegram_escape(kitob.nomi)}</b> navbatiga qo'shildingiz.\n"
        f"Navbatdagi o'rningiz: <b>{natija.orin}</b>.",
    )


def _kitoblarim(bot, chat_id, telegram_id):
    oquvchi = _reader(bot, telegram_id)
    if not oquvchi:
        return _send(bot, chat_id, "Avval /start orqali ro'yxatdan o'ting.")
    qs = Berish.objects.filter(
        organization=bot.organization, oquvchi=oquvchi, qaytarilgan_sana__isnull=True
    ).select_related("kitob", "nusxa")
    if not qs:
        return _send(bot, chat_id, "Sizda hozir faol kitob yo'q.")
    matn = "📖 <b>Mening kitoblarim</b>\n\n"
    for berish in qs:
        inv = f" ({berish.nusxa.inventar_raqami})" if berish.nusxa else " (asli)"
        matn += (
            f"• <b>{telegram_escape(berish.kitob.nomi)}</b>{inv}\n"
            f"  Qaytarish: <b>{berish.qaytarish_muddati}</b>\n"
        )
    _send(bot, chat_id, matn)


def _navbatlarim(bot, chat_id, telegram_id):
    oquvchi = _reader(bot, telegram_id)
    if not oquvchi:
        return _send(bot, chat_id, "Avval /start orqali ro'yxatdan o'ting.")
    qs = Navbat.objects.filter(
        organization=bot.organization,
        oquvchi=oquvchi,
        holati__in=["kutmoqda", "taklif_qilindi"],
    ).select_related("kitob")
    if not qs:
        return _send(bot, chat_id, "Faol navbatlaringiz yo'q.")
    matn = "⏳ <b>Navbatlarim</b>\n\n"
    for navbat in qs:
        matn += f"• {telegram_escape(navbat.kitob.nomi)} — {navbat.get_holati_display()}\n"
    _send(bot, chat_id, matn)


def _jarimalarim(bot, chat_id, telegram_id):
    oquvchi = _reader(bot, telegram_id)
    if not oquvchi:
        return _send(bot, chat_id, "Avval /start orqali ro'yxatdan o'ting.")
    qs = Jarima.objects.filter(
        organization=bot.organization, berish__oquvchi=oquvchi, tolandimi=False
    ).select_related("berish__kitob")
    if not qs:
        return _send(bot, chat_id, "To'lanmagan jarimangiz yo'q. ✅")
    jami = sum(j.summa for j in qs)
    matn = f"💰 <b>To'lanmagan jarimalar</b>\n\nJami: <b>{jami}</b> so'm\n\n"
    for jarima in qs:
        matn += (
            f"• {telegram_escape(jarima.berish.kitob.nomi)} — "
            f"{jarima.summa} so'm ({jarima.kechikkan_kunlar} kun)\n"
        )
    _send(bot, chat_id, matn)


def _bandlarim(bot, chat_id, telegram_id):
    oquvchi = _reader(bot, telegram_id)
    if not oquvchi:
        return _send(bot, chat_id, "Avval /start orqali ro'yxatdan o'ting.")
    qs = BandQilish.objects.filter(
        organization=bot.organization, oquvchi=oquvchi, holati="kutmoqda"
    ).select_related("kitob")
    if not qs:
        return _send(bot, chat_id, "Faol band so'rovingiz yo'q.")
    matn = "🔒 <b>Band qilganlarim</b>\n\n"
    for band in qs:
        matn += f"• {telegram_escape(band.kitob.nomi)} — tasdiqlash kutilmoqda\n"
    _send(bot, chat_id, matn)


def _statistika(bot, chat_id, telegram_id):
    if not _staff(bot, telegram_id):
        return _send(bot, chat_id, "Bu bo'lim faqat kutubxonachilar uchun.")
    org = bot.organization
    from nusxa.models import Nusxa

    matn = (
        f"📊 <b>{telegram_escape(org.nomi)}</b>\n\n"
        f"📚 Kitoblar: <b>{Kitob.objects.filter(organization=org).count()}</b>\n"
        f"📦 Nusxalar: <b>{Nusxa.objects.filter(organization=org).count()}</b>\n"
        f"👥 O'quvchilar: <b>{Oquvchi.objects.filter(organization=org, faol=True).count()}</b>\n"
        f"📖 Faol berishlar: <b>{Berish.objects.filter(organization=org, qaytarilgan_sana__isnull=True).count()}</b>\n"
        f"⏳ Faol navbatlar: <b>{Navbat.objects.filter(organization=org, holati__in=['kutmoqda', 'taklif_qilindi']).count()}</b>\n"
        f"🔔 Kutilayotgan bandlar: <b>{BandQilish.objects.filter(organization=org, holati='kutmoqda').count()}</b>\n"
        f"💰 To'lanmagan jarimalar: <b>{Jarima.objects.filter(organization=org, tolandimi=False).count()}</b>"
    )
    _send(bot, chat_id, matn)


def _bandlar_royxati(bot, chat_id, telegram_id):
    if not _staff(bot, telegram_id):
        return _send(bot, chat_id, "Bu bo'lim faqat kutubxonachilar uchun.")
    qs = BandQilish.objects.filter(
        organization=bot.organization, holati="kutmoqda"
    ).select_related("kitob", "oquvchi")[:10]
    if not qs:
        return _send(bot, chat_id, "Kutilayotgan band so'rovlar yo'q.")
    for band in qs:
        rol = "o'qituvchi" if band.oquvchi.rol == "oqituvchi" else "o'quvchi"
        matn = (
            f"🔔 <b>{telegram_escape(band.kitob.nomi)}</b>\n"
            f"So'rovchi: {telegram_escape(band.oquvchi.fish)} ({rol})\n"
            f"Sana: {timezone.localtime(band.so_rov_sanasi):%d.%m.%Y %H:%M}"
        )
        _send(
            bot,
            chat_id,
            matn,
            _inline(
                [
                    [
                        {"text": "✅ Tasdiqlash", "callback_data": f"band_ok:{band.pk}"},
                        {"text": "❌ Rad etish", "callback_data": f"band_no:{band.pk}"},
                    ]
                ]
            ),
        )


def _band_qaror(bot, chat_id, telegram_id, band_id, tasdiq, callback_id=None):
    xodim = _staff(bot, telegram_id)
    if not xodim:
        _send(bot, chat_id, "Ruxsat yo'q.")
        return
    band = BandQilish.objects.filter(
        organization=bot.organization, pk=band_id, holati="kutmoqda"
    ).first()
    if not band:
        _send(bot, chat_id, "So'rov topilmadi yoki allaqachon yopilgan.")
        return
    from kitob.services import band_qilishni_rad_et, band_qilishni_tasdiqla

    try:
        if tasdiq:
            band_qilishni_tasdiqla(band, xodim.user, "Telegram bot orqali")
            _send(bot, chat_id, f"✅ Tasdiqlandi: {telegram_escape(band.kitob.nomi)}")
        else:
            band_qilishni_rad_et(band, xodim.user, "Telegram bot orqali rad etildi")
            _send(bot, chat_id, f"❌ Rad etildi: {telegram_escape(band.kitob.nomi)}")
    except Exception as xato:
        _send(bot, chat_id, f"Amal bajarilmadi: {telegram_escape(xato)}")
    if callback_id:
        try:
            answer_callback_query(bot.get_token(), callback_id)
        except Exception:
            pass


def _qaytarish(bot, chat_id, telegram_id, inventar):
    xodim = _staff(bot, telegram_id)
    if not xodim:
        return _send(bot, chat_id, "Bu amal faqat kutubxonachilar uchun.")
    from berish.models import Berish as BerishModel
    from berish.services import kitob_qaytar
    from nusxa.models import Nusxa

    nusxa = Nusxa.objects.filter(
        organization=bot.organization, inventar_raqami=inventar.strip()
    ).first()
    if not nusxa:
        return _send(bot, chat_id, "Bunday inventar raqamli nusxa topilmadi.")
    berish = BerishModel.objects.filter(
        organization=bot.organization, nusxa=nusxa, qaytarilgan_sana__isnull=True
    ).first()
    if not berish:
        return _send(bot, chat_id, "Bu nusxa hozir hech kimda emas.")
    try:
        berish, jarima, _ = kitob_qaytar(berish, xodim.user)
    except Exception as xato:
        return _send(bot, chat_id, f"Qaytarish xatosi: {telegram_escape(xato)}")
    matn = (
        f"✅ <b>{telegram_escape(berish.kitob.nomi)}</b> qaytarib olindi.\n"
        f"O'quvchi: {telegram_escape(berish.oquvchi.fish)}"
    )
    if jarima:
        matn += f"\n💰 Jarima: <b>{jarima.summa}</b> so'm"
    _send(bot, chat_id, matn)


def _ulash(bot, chat_id, telegram_id, kod):
    if not kod:
        return _send(bot, chat_id, "Format: /ulash KOD")
    azolik = Membership.objects.filter(
        organization=bot.organization,
        link_code=kod,
        link_code_expires__gt=timezone.now(),
        faol=True,
    ).first()
    if not azolik:
        return _send(bot, chat_id, "Kod yaroqsiz yoki muddati o'tgan.")
    boshqa = (
        Membership.objects.filter(
            organization=bot.organization, telegram_id=telegram_id
        )
        .exclude(pk=azolik.pk)
        .exists()
    )
    if boshqa:
        return _send(bot, chat_id, "Bu Telegram akkaunt boshqa xodimga bog'langan.")
    if azolik.telegram_id and azolik.telegram_id != telegram_id:
        return _send(bot, chat_id, "Bu kod boshqa Telegram akkauntga bog'langan.")
    azolik.telegram_id = telegram_id
    azolik.link_code = ""
    azolik.link_code_expires = None
    azolik.save(update_fields=["telegram_id", "link_code", "link_code_expires"])
    _send(
        bot,
        chat_id,
        f"✅ Telegram ulandi. Xush kelibsiz, {telegram_escape(azolik.user.full_name)}!",
        STAFF_MENU,
    )


def _yordam(bot, chat_id):
    _send(
        bot,
        chat_id,
        "ℹ️ <b>Yordam</b>\n\n"
        "/start — bosh menyu\n"
        "/qidiruv so'z — kitob qidirish\n"
        "/kitoblarim — faol kitoblar\n"
        "/navbatlarim — navbatlar\n"
        "/jarimalarim — jarimalar\n"
        "/bandlarim — band so'rovlar\n"
        "/ulash KOD — xodim Telegramini ulash (kutubxonachi)",
    )


def _text(bot, message):
    chat_id = message["chat"]["id"]
    telegram_id = message["from"]["id"]
    matn = (message.get("text") or "").strip()
    if not matn:
        return

    sessiya = _session(bot, telegram_id)
    if sessiya and not matn.startswith("/"):
        _ariza_text(bot, message, sessiya)
        return

    if matn.startswith("/start"):
        return _start(bot, message)
    if matn.startswith("/ulash"):
        qismlar = matn.split(maxsplit=1)
        return _ulash(bot, chat_id, telegram_id, qismlar[1].strip() if len(qismlar) > 1 else "")
    if matn.startswith("/qidiruv"):
        qismlar = matn.split(maxsplit=1)
        return _qidiruv(bot, chat_id, telegram_id, qismlar[1].strip() if len(qismlar) > 1 else "")
    if matn.startswith("/kitoblarim") or matn == "📖 Mening kitoblarim":
        return _kitoblarim(bot, chat_id, telegram_id)
    if matn.startswith("/navbatlarim") or matn == "⏳ Navbatlarim":
        return _navbatlarim(bot, chat_id, telegram_id)
    if matn.startswith("/jarimalarim") or matn == "💰 Jarimalarim":
        return _jarimalarim(bot, chat_id, telegram_id)
    if matn.startswith("/bandlarim") or matn == "🔒 Band qilganlarim":
        return _bandlarim(bot, chat_id, telegram_id)
    if matn.startswith("/bandlar") or matn == "🔔 Band so'rovlar":
        return _bandlar_royxati(bot, chat_id, telegram_id)
    if matn.startswith("/statistika") or matn == "📊 Statistika":
        return _statistika(bot, chat_id, telegram_id)
    if matn.startswith("/qaytarish") or matn == "↩️ Qaytarish":
        if not _staff(bot, telegram_id):
            return _send(bot, chat_id, "Bu amal faqat kutubxonachilar uchun.")
        _set_session(bot, telegram_id, chat_id, "qaytarish")
        return _send(bot, chat_id, "Qaytarilayotgan nusxaning inventar raqamini kiriting:")
    if matn.startswith("/yordam") or matn == "ℹ️ Yordam":
        return _yordam(bot, chat_id)
    if matn == "🔎 Kitob qidirish":
        _set_session(bot, telegram_id, chat_id, "qidiruv")
        return _send(bot, chat_id, "Kitob nomi, muallifi yoki ISBNini kiriting:")
    if matn == "📚 Kategoriyalar":
        labels = dict(Kitob.JANR_CHOICES)
        rows = []
        for janr in Kitob.objects.filter(organization=bot.organization).values_list(
            "janr", flat=True
        ).distinct():
            rows.append(
                [
                    {
                        "text": labels.get(janr, janr),
                        "callback_data": f"janr:{janr}",
                    }
                ]
            )
        if not rows:
            return _send(bot, chat_id, "Hozircha kitob yo'q.")
        return _send(bot, chat_id, "Kategoriyani tanlang:", _inline(rows))
    if _staff(bot, telegram_id):
        return _send(bot, chat_id, "Kerakli bo'limni tanlang.", STAFF_MENU)
    return _send(bot, chat_id, "Kerakli bo'limni tanlang.", READER_MENU)


def _callback(bot, callback):
    chat_id = callback["message"]["chat"]["id"]
    telegram_id = callback["from"]["id"]
    data = callback.get("data", "")
    callback_id = callback.get("id")
    if data.startswith("rol:"):
        _ariza_rol(bot, chat_id, telegram_id, data.split(":", 1)[1])
    elif data.startswith("janr:"):
        janr = data.split(":", 1)[1]
        labels = dict(Kitob.JANR_CHOICES)
        kitoblar = (
            Kitob.objects.filter(organization=bot.organization, janr=janr)
            .annotate(mavjud_soni=Count("nusxalar", filter=Q(nusxalar__holati="mavjud")))
            .order_by("nomi")[:10]
        )
        rows = [
            [
                {
                    "text": f"{'🟢' if k.mavjud_soni else '🔴'} {k.nomi[:45]}",
                    "callback_data": f"kitob:{k.pk}",
                }
            ]
            for k in kitoblar
        ]
        _send(
            bot,
            chat_id,
            f"{labels.get(janr, janr)} bo'limidagi kitoblar:",
            _inline(rows) if rows else None,
        )
    elif data.startswith("kitob:"):
        _kitob_karta(bot, chat_id, telegram_id, data.split(":", 1)[1], callback_id)
    elif data.startswith("band_ok:"):
        _band_qaror(bot, chat_id, telegram_id, data.split(":", 1)[1], True, callback_id)
    elif data.startswith("band_no:"):
        _band_qaror(bot, chat_id, telegram_id, data.split(":", 1)[1], False, callback_id)
    elif data.startswith("band:"):
        _band_qilish(bot, chat_id, telegram_id, data.split(":", 1)[1])
    elif data.startswith("navbat:"):
        _navbatga_qosh(bot, chat_id, telegram_id, data.split(":", 1)[1])


def handle_update(bot, update):
    if "message" in update:
        _text(bot, update["message"])
    elif "callback_query" in update:
        _callback(bot, update["callback_query"])
    return True
