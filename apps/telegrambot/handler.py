"""Kutubxona botining webhook handleri.

Har bir so'rov faqat `bot.organization` doirasida ishlaydi. Foydalanuvchi
yuborgan ID'lar (kitob, band, navbat) har doim shu kutubxona bo'yicha
qayta tekshiriladi — boshqa kutubxona obyektiga murojaat qilib bo'lmaydi.
"""

import hashlib
import re
from datetime import date

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.exceptions import ErrorDetail, ValidationError

from berish.models import Berish
from config.telegram import telegram_escape
from jarima.models import Jarima
from kitob.models import BandQilish, Kitob
from navbat.models import Navbat
from organization.models import Membership, Organization
from oquvchi.constants import FAN_LIMIT, FANLAR, FISH_RE, SINF_RE, format_xatolari
from oquvchi.models import Ariza, Oquvchi
from oquvchi.search import tolerant_q
from reviews import services as reviews

from .client import answer_callback_query, answer_inline_query
from .models import TelegramSession
from .staff_link import code_from_start_payload, link_staff
from .subscription import CHECK_CALLBACK, gate_keyboard, gate_text, subscription_gate
from .services import xabar_yubor

TELEFON_RE = re.compile(r"^\+998\d{9}$")


def _normalize_phone(raw):
    """Accept '+998901234567', '998 90 123 45 67', '00998...', '901234567'; return '+998XXXXXXXXX' or None."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("00998"):
        digits = digits[2:]
    if len(digits) == 9:
        digits = "998" + digits
    phone = "+" + digits
    return phone if TELEFON_RE.match(phone) else None

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

# Xodim ham, o'quvchi ham bo'lgan foydalanuvchi ikkala bo'limga ham kirishi kerak.
QOSHMA_MENU = {
    "keyboard": READER_MENU["keyboard"] + STAFF_MENU["keyboard"][:-1],
    "resize_keyboard": True,
}

# Ariza/qidiruv bosqichida tugma matni maydonga yozilmasligi uchun.
MENYU_TUGMALARI = frozenset(
    tugma["text"]
    for menyu in (READER_MENU, STAFF_MENU)
    for qator in menyu["keyboard"]
    for tugma in qator
)

BANDLAR_SAHIFA_O_LCHAMI = settings.REST_FRAMEWORK.get("PAGE_SIZE", 20)
BANDLAR_CHEKLAMI = 200

ARIZA_SAVOL_FISH = "Ism va familiyangizni kiriting:"
ARIZA_SAVOL_TELEFON = "Telefon raqamingizni +998XXXXXXXXX formatida kiriting:"
ARIZA_SAVOL_KASB = (
    "Qaysi fanlarni o'qitasiz? Ikkitagacha fan nomini vergul bilan yozing "
    "(masalan: Matematika, Fizika)."
)
ARIZA_SAVOL_SINF = "Sinfingizni kiriting (masalan: 7-A):"
QUESTION_ADDRESS = (
    "Yashash manzilingizni kiriting (masalan: Toshkent sh., Chilonzor tumani, 5-kvartal, 12-uy):"
)
QUESTION_BIRTH_DATE = "Tug'ilgan sanangizni KK.OO.YYYY formatida kiriting (masalan: 15.03.2001):"
# Library organizations ask these two after the phone instead of class/subject.
STEP_ADDRESS = "application_address"
STEP_BIRTH_DATE = "application_birth_date"
APPLICATION_STEP_PREFIXES = ("ariza_", "application_")
ARIZA_SAVOLLARI = {
    "ariza_fish": ARIZA_SAVOL_FISH,
    "ariza_telefon": ARIZA_SAVOL_TELEFON,
    "ariza_kasb": ARIZA_SAVOL_KASB,
    "ariza_sinf": ARIZA_SAVOL_SINF,
    STEP_ADDRESS: QUESTION_ADDRESS,
    STEP_BIRTH_DATE: QUESTION_BIRTH_DATE,
}
BIRTH_DATE_RE = re.compile(r"^(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})$")


def _parse_birth_date(text):
    """'15.03.2001' (also with '-' or '/') -> date, or None if it is not a plausible birth date."""
    match = BIRTH_DATE_RE.fullmatch((text or "").strip())
    if not match:
        return None
    day, month, year = (int(part) for part in match.groups())
    try:
        value = date(year, month, day)
    except ValueError:
        return None
    return value if date(1900, 1, 1) <= value <= date.today() else None


def _is_library(bot):
    return bot.organization.type == Organization.TYPE_LIBRARY

# Xizmatlar `ValidationError({"error": kod, "detail": ...})` ko'taradi.
# Kodlarni foydalanuvchiga tushunarli matn bilan almashtiramiz.
XATO_XABARLARI = {
    "allaqachon_band_qilingan": "Bu kitob boshqa o'quvchi uchun band qilingan.",
    "kitob_band_qilingan": (
        "Bu kitob band qilingan — uni faqat kutubxonachi tasdiqlagandan keyin berish mumkin."
    ),
    "allaqachon_berilgan": "Bu kitob allaqachon sizda bor.",
    "barcha_nusxalar_berilgan": "Hozir bu amalni bajarib bo'lmaydi. Iltimos, keyinroq urinib ko'ring.",
    "limit_oshdi": "Siz allaqachon eng ko'p kitob olgansiz.",
    "tolanmagan_jarima": "Sizda to'lanmagan jarima bor.",
    "oquvchi_bloklangan": "Sizning kartangiz bloklangan.",
    "nusxa_band": "Hozir bu amalni bajarib bo'lmaydi. Iltimos, keyinroq urinib ko'ring.",
    "so_rov_yopilgan": "Bu so'rov allaqachon yopilgan.",
    "berish_mumkin_emas": "Bu kitobni hozir berib bo'lmaydi.",
    "allaqachon_qaytarilgan": "Bu kitob allaqachon qaytarib olingan.",
    "ruxsat_yuq": "Bu amalga ruxsatingiz yo'q.",
}


def _detail_matnlari(detail):
    """ValidationError.detail (dict/list/ErrorDetail) ichidagi matnlarni oladi."""
    if isinstance(detail, ErrorDetail):
        yield str(detail)
    elif isinstance(detail, dict):
        for qiymat in detail.values():
            yield from _detail_matnlari(qiymat)
    elif isinstance(detail, (list, tuple)):
        for qiymat in detail:
            yield from _detail_matnlari(qiymat)
    elif detail is not None:
        yield str(detail)


def _xato_matni(xato) -> str:
    """Texnik `ErrorDetail(...)` o'rniga odam o'qiydigan xabar qaytaradi."""
    detail = xato.detail if isinstance(xato, ValidationError) else xato
    matnlar = []
    if isinstance(detail, dict):
        for kalit in ("error", "kod", "code"):
            kod = detail.get(kalit)
            if str(kod) in XATO_XABARLARI:
                return XATO_XABARLARI[str(kod)]
        izoh = detail.get("detail", detail.get("xato"))
        if izoh is not None:
            matnlar = list(_detail_matnlari(izoh))
        if not matnlar:
            matnlar = [
                matn for matn in _detail_matnlari(detail)
                if matn not in XATO_XABARLARI
            ]
    else:
        matnlar = list(_detail_matnlari(detail))
    if not matnlar:
        return "Amal bajarilmadi."
    return telegram_escape("; ".join(dict.fromkeys(matnlar)))


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
        # Ikkala rolga ega foydalanuvchi o'quvchi bo'limlarini ham yo'qotmasin.
        if _reader(bot, telegram_id):
            return QOSHMA_MENU
        return STAFF_MENU
    return READER_MENU


def _qayta_ariza_kerak(bot, telegram_id):
    """Eski formatdagi ariza/azo qaytadan ariza yuborishi kerakmi?"""
    return Oquvchi.objects.filter(
        organization=bot.organization,
        telegram_id=telegram_id,
        qayta_ariza_kerak=True,
    ).exists() or Ariza.objects.filter(
        organization=bot.organization,
        telegram_id=telegram_id,
        qayta_ariza_kerak=True,
    ).exists()


QAYTA_ARIZA_XABARI = (
    "⚠️ Oldingi arizangiz belgilangan formatda to'ldirilmagan.\n\n"
    "Yangi qoidalarga muvofiq arizani boshidan, aynan ko'rsatilgan "
    "formatda qaytadan yuborishingiz kerak. Rolingizni tanlang:"
)

FORMAT_XATO_XABARI = (
    "❌ Ma'lumot belgilangan formatda yozilmadi.\n\n"
    "Ism-familiya «Ali Valiyev», telefon «+998901234567», "
    "sinf «7-A» ko'rinishida bo'lishi kerak. Fanlarni ro'yxatdan tanlang.\n\n"
    "Arizani boshidan qayta to'ldiring. Rolingizni tanlang:"
)


# A library has no roles: the same restart messages end with a single "join" button.
LIBRARY_TEXTS = {
    QAYTA_ARIZA_XABARI: (
        "⚠️ Oldingi arizangiz belgilangan formatda to'ldirilmagan.\n\n"
        "Arizani boshidan, aynan ko'rsatilgan formatda qaytadan yuboring:"
    ),
    FORMAT_XATO_XABARI: (
        "❌ Ma'lumot belgilangan formatda yozilmadi.\n\n"
        "Ism-familiya «Ali Valiyev», telefon «+998901234567» ko'rinishida bo'lishi kerak.\n\n"
        "Arizani boshidan qayta to'ldiring:"
    ),
}
JOIN_BUTTON = [[{"text": "📝 A'zo bo'lish", "callback_data": "rol:oquvchi"}]]


def _rol_tanlash(bot, chat_id, matn):
    if _is_library(bot):
        _send(bot, chat_id, LIBRARY_TEXTS.get(matn, matn), _inline(JOIN_BUTTON))
        return
    _send(
        bot,
        chat_id,
        matn,
        _inline(
            [
                [
                    {"text": "🎓 O'quvchi", "callback_data": "rol:oquvchi"},
                    {"text": "👨‍🏫 O'qituvchi", "callback_data": "rol:oqituvchi"},
                ]
            ]
        ),
    )


def _start(bot, message):
    chat_id = message["chat"]["id"]
    telegram_id = message["from"]["id"]
    _clear_session(bot, telegram_id)
    parts = (message.get("text") or "").split(maxsplit=1)
    link_code = code_from_start_payload(parts[1] if len(parts) > 1 else "")
    if link_code:
        return _ulash(bot, chat_id, telegram_id, link_code)
    qayta_ariza = _qayta_ariza_kerak(bot, telegram_id)
    oquvchi = _reader(bot, telegram_id)
    xodim = _staff(bot, telegram_id)
    if xodim and oquvchi and not qayta_ariza:
        _send(
            bot,
            chat_id,
            f"Salom, <b>{telegram_escape(xodim.user.full_name)}</b>!\n"
            "Siz kutubxonachi ham, o'quvchi ham sifatida ro'yxatdasiz. "
            "Kerakli bo'limni tanlang.",
            _menu(bot, telegram_id),
        )
        return
    if oquvchi and not qayta_ariza:
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
    if ariza and ariza.holati == "kutmoqda" and not qayta_ariza:
        _send(
            bot,
            chat_id,
            "Arizangiz ko'rib chiqilmoqda. Tasdiqlangach xabar beramiz.",
            {"remove_keyboard": True},
        )
        return
    if qayta_ariza:
        # Eski (noto'g'ri formatdagi) arizalar yangi arizaga to'siq bo'lmasin.
        Ariza.objects.filter(
            organization=bot.organization, telegram_id=telegram_id
        ).delete()
        _rol_tanlash(bot, chat_id, QAYTA_ARIZA_XABARI)
        return
    if _is_library(bot):
        _send(
            bot,
            chat_id,
            "◈ <b>KUTUBXONA</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "A'zo bo'lish uchun tugmani bosing:",
            _inline(JOIN_BUTTON),
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
    if rol not in ("oquvchi", "oqituvchi") or (_is_library(bot) and rol != "oquvchi"):
        return
    qayta_ariza = _qayta_ariza_kerak(bot, telegram_id)
    bandlangan = _reader(bot, telegram_id) and not qayta_ariza
    if not qayta_ariza and Ariza.objects.filter(
        organization=bot.organization,
        telegram_id=telegram_id,
        holati="kutmoqda",
        qayta_ariza_kerak=False,
    ).exists():
        bandlangan = True
    if bandlangan or _staff(bot, telegram_id):
        _send(bot, chat_id, "Siz allaqachon ro'yxatdan o'tgansiz.", _menu(bot, telegram_id))
        return
    if qayta_ariza:
        Ariza.objects.filter(
            organization=bot.organization, telegram_id=telegram_id
        ).delete()
    _set_session(bot, telegram_id, chat_id, "ariza_fish", {"rol": rol})
    _send(bot, chat_id, ARIZA_SAVOL_FISH, {"remove_keyboard": True})


def _submit_application(bot, chat_id, telegram_id, **fields):
    """Replace the user's old applications with a new pending one and confirm it."""
    if Ariza.objects.filter(
        organization=bot.organization,
        telegram_id=telegram_id,
        holati="kutmoqda",
        qayta_ariza_kerak=False,
    ).exists():
        _send(bot, chat_id, "Arizangiz allaqachon ko'rib chiqilmoqda.")
        _clear_session(bot, telegram_id)
        return
    Ariza.objects.filter(organization=bot.organization, telegram_id=telegram_id).delete()
    Ariza.objects.create(organization=bot.organization, telegram_id=telegram_id, **fields)
    _clear_session(bot, telegram_id)
    _send(
        bot,
        chat_id,
        "✅ Arizangiz qabul qilindi. Kutubxonachi tasdiqlagach xabar beramiz.",
        {"remove_keyboard": True},
    )


def _ariza_text(bot, message, sessiya):
    chat_id = message["chat"]["id"]
    telegram_id = message["from"]["id"]
    matn = (message.get("text") or "").strip()
    data = sessiya.data or {}
    step = sessiya.step
    if step == "ariza_fish":
        if len(matn) < 3 or len(matn) > 130 or not FISH_RE.fullmatch(matn):
            _clear_session(bot, telegram_id)
            _rol_tanlash(bot, chat_id, FORMAT_XATO_XABARI)
            return
        data["fish"] = matn
        _set_session(bot, telegram_id, chat_id, "ariza_telefon", data)
        _send(bot, chat_id, ARIZA_SAVOL_TELEFON)
        return
    if step == "ariza_telefon":
        telefon = _normalize_phone(matn)
        if not telefon:
            _send(
                bot,
                chat_id,
                "Telefon raqam noto'g'ri. Masalan: +998901234567 yoki 90 123 45 67.\n"
                "Bekor qilish: /start",
            )
            return
        if Oquvchi.objects.filter(
            organization=bot.organization, telefon=telefon
        ).exists():
            _send(
                bot,
                chat_id,
                "Bu telefon raqam bilan o'quvchi allaqachon ro'yxatda. "
                "Boshqa raqam yuboring yoki /start bosib, mavjud hisobingizni ulang.",
            )
            return
        data["telefon"] = telefon
        if _is_library(bot):
            _set_session(bot, telegram_id, chat_id, STEP_ADDRESS, data)
            _send(bot, chat_id, QUESTION_ADDRESS)
        elif data.get("rol") == "oqituvchi":
            _set_session(bot, telegram_id, chat_id, "ariza_kasb", data)
            _send(bot, chat_id, ARIZA_SAVOL_KASB)
        else:
            _set_session(bot, telegram_id, chat_id, "ariza_sinf", data)
            _send(bot, chat_id, ARIZA_SAVOL_SINF)
        return
    if step == STEP_ADDRESS:
        if not 5 <= len(matn) <= 255:
            _send(bot, chat_id, f"Manzil 5 dan 255 belgigacha bo'lishi kerak.\n\n{QUESTION_ADDRESS}")
            return
        data["manzil"] = matn
        _set_session(bot, telegram_id, chat_id, STEP_BIRTH_DATE, data)
        _send(bot, chat_id, QUESTION_BIRTH_DATE)
        return
    if step == STEP_BIRTH_DATE:
        birth_date = _parse_birth_date(matn)
        if not birth_date:
            _send(bot, chat_id, f"Sana noto'g'ri.\n\n{QUESTION_BIRTH_DATE}")
            return
        # Name and phone were validated at their own steps.
        _submit_application(
            bot,
            chat_id,
            telegram_id,
            fish=data["fish"],
            telefon=data["telefon"],
            rol="oquvchi",
            sinf=None,
            kasb="",
            manzil=data.get("manzil", ""),
            tugilgan_sana=birth_date,
        )
        return
    if step in ("ariza_sinf", "ariza_kasb"):
        rol = data.get("rol", "oquvchi")
        if rol == "oqituvchi":
            fanlar = [fan.strip() for fan in matn.split(",") if fan.strip()]
            togri = (
                1 <= len(fanlar) <= FAN_LIMIT
                and len(matn) <= 60
                and all(f in FANLAR for f in fanlar)
            )
            data["kasb"] = ", ".join(fanlar)
        else:
            togri = len(matn) <= 30 and bool(SINF_RE.fullmatch(matn))
            data["sinf"] = matn
        if not togri or format_xatolari(
            fish=data.get("fish", ""),
            telefon=data.get("telefon", ""),
            rol=rol,
            sinf=data.get("sinf", ""),
            kasb=data.get("kasb", ""),
        ):
            _clear_session(bot, telegram_id)
            _rol_tanlash(bot, chat_id, FORMAT_XATO_XABARI)
            return
        _submit_application(
            bot,
            chat_id,
            telegram_id,
            fish=data["fish"],
            telefon=data["telefon"],
            rol=rol,
            sinf=data.get("sinf") if rol == "oquvchi" else None,
            kasb=data.get("kasb", "") if rol == "oqituvchi" else "",
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


def _search_books(bot, q, limit, offset=0):
    """Books of the bot's library matching title, author or ISBN, with copy availability counts.

    An empty `q` lists the whole catalogue, available books first.
    """
    qs = Kitob.objects.filter(organization=bot.organization)
    if q:
        qs = qs.filter(tolerant_q(["nomi", "muallif", "isbn"], q))
    qs = qs.annotate(
        mavjud_soni=Count("nusxalar", filter=Q(nusxalar__holati="mavjud")),
        jami_soni=Count("nusxalar"),
    )
    qs = qs.order_by("-mavjud_soni", "nomi", "pk") if not q else qs.order_by("nomi", "pk")
    return qs[offset : offset + limit]


INLINE_CACHE_SECONDS = 30
INLINE_PAGE_SIZE = 20


def _book_action_rows(kitob_pk, available, total):
    """Reserve button, plus a queue button when copies exist but none is free.

    Same rule as the aiogram bot: a book without any copy would turn a queue
    entry into an immediate loan, so it gets no queue button.
    """
    rows = [[{"text": "🔒 Band qilish", "callback_data": f"band:{kitob_pk}"}]]
    if total and not available:
        rows.append([{"text": "⏳ Navbatga yozilish", "callback_data": f"navbat:{kitob_pk}"}])
    return rows


def _inline_query(bot, inline):
    """Answer `@bot text` queries with matching books, only if the library enabled `search_inline`."""
    if not bot.organization.has_capability("search_inline"):
        return
    token = bot.get_token()
    query_id = inline["id"]
    telegram_id = inline["from"]["id"]
    q = (inline.get("query") or "").strip()
    if not (_reader(bot, telegram_id) or _staff(bot, telegram_id)):
        # The catalogue is for members only; point strangers to registration.
        answer_inline_query(
            token, query_id, [], cache_time=0,
            button={"text": "Ro'yxatdan o'tish", "start_parameter": "start"},
        )
        return
    if len(q) == 1:
        answer_inline_query(token, query_id, [], cache_time=5)
        return
    # Results are the same for every member, so share them through Redis for a short while
    # (availability counts may lag by up to INLINE_CACHE_SECONDS).
    offset = int(inline["offset"]) if str(inline.get("offset") or "").isdigit() else 0
    cache_key = f"inline:{bot.organization_id}:{offset}:{hashlib.md5(q.lower().encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached is None:
        cached = _inline_results(bot, q, offset)
        cache.set(cache_key, cached, INLINE_CACHE_SECONDS)
    results, has_more = cached
    answer_inline_query(
        token, query_id, results, cache_time=INLINE_CACHE_SECONDS,
        next_offset=str(offset + INLINE_PAGE_SIZE) if has_more else "",
    )


def _inline_results(bot, q, offset=0):
    """One page of article results plus whether more books follow (Telegram allows max 50 per answer)."""
    results = []
    books = list(_search_books(bot, q, INLINE_PAGE_SIZE + 1, offset))
    has_more = len(books) > INLINE_PAGE_SIZE
    for kitob in books[:INLINE_PAGE_SIZE]:
        holat = f"🟢 Mavjud: {kitob.mavjud_soni}/{kitob.jami_soni}" if kitob.mavjud_soni else "🔴 Hozir mavjud emas"
        results.append(
            {
                "type": "article",
                "id": str(kitob.pk),
                "title": kitob.nomi[:100],
                "description": f"{kitob.muallif or '—'} · {holat}"[:200],
                "input_message_content": {
                    "message_text": (
                        f"📖 <b>{telegram_escape(kitob.nomi)}</b>\n"
                        f"✍️ {telegram_escape(kitob.muallif or '—')}\n{holat}"
                    ),
                    "parse_mode": "HTML",
                },
                # Reserve / queue straight from the posted message.
                "reply_markup": _inline(_book_action_rows(kitob.pk, kitob.mavjud_soni, kitob.jami_soni)),
            }
        )
    return results, has_more


def _qidiruv(bot, chat_id, telegram_id, q):
    oquvchi = _reader(bot, telegram_id)
    if not oquvchi:
        _send(bot, chat_id, "Avval /start orqali ro'yxatdan o'ting.")
        return
    if not q:
        _send(bot, chat_id, "Qidiruv so'zini kiriting.")
        return
    kitoblar = _search_books(bot, q, 10)
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


def _kitob_karta(bot, chat_id, telegram_id, kitob_id):
    kitob = Kitob.objects.filter(organization=bot.organization, pk=kitob_id).first()
    if not kitob:
        _send(bot, chat_id, "Kitob topilmadi.")
        return
    faol_berishlar = list(
        Berish.objects.filter(
            organization=bot.organization, kitob=kitob, qaytarilgan_sana__isnull=True
        ).select_related("oquvchi", "nusxa")
    )
    kimdadimi = bool(faol_berishlar)
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
    # Nusxa yo'qligi/berilganligi haqida foydalanuvchiga xabar berilmaydi.
    # Faqat olish mumkin bo'lganda ijobiy ma'lumot ko'rsatiladi.
    if mavjud:
        matn += "✅ Hozir kutubxonada mavjud.\n"
    if kimdadimi:
        matn += "\n<b>Hozir kimda:</b>\n"
        for berish in faol_berishlar[:5]:
            kim = berish.oquvchi
            sinf = kim.kasb if kim.rol == "oqituvchi" else kim.sinf
            matn += (
                f"• {telegram_escape(kim.fish)}"
                f"{f' ({telegram_escape(sinf)})' if sinf else ''} — "
                f"{berish.qaytarish_muddati}\n"
            )
    info = reviews.summary(kitob)
    if info["count"]:
        matn += f"\n⭐ {info['avg']} / 5 · {info['count']} ta baho\n"
    rows = _book_action_rows(kitob.pk, mavjud, jami)
    rows.append(_review_row(bot, telegram_id, kitob, info))
    _send(bot, chat_id, matn, _inline(rows))


def _review_row(bot, telegram_id, kitob, info):
    row = [{"text": f"💬 Fikrlar ({info['count']})", "callback_data": f"rv_list:{kitob.pk}"}]
    reader = _reader(bot, telegram_id)
    if reader and reviews.has_read(reader, kitob):
        row.append({"text": "✍️ Fikr qoldirish", "callback_data": f"rv_new:{kitob.pk}"})
    return row


def _review_book(bot, chat_id, telegram_id, book_id):
    """The book and reader for a review action, or None after telling the user why."""
    kitob = Kitob.objects.filter(organization=bot.organization, pk=book_id).first()
    reader = _reader(bot, telegram_id)
    if not kitob:
        _send(bot, chat_id, "Kitob topilmadi.")
        return None, None
    if not reader or not reviews.has_read(reader, kitob):
        _send(bot, chat_id, reviews.NOT_ALLOWED)
        return None, None
    return kitob, reader


def _review_callback(bot, chat_id, telegram_id, data):
    parts = data.split(":")
    action, book_id = parts[0], parts[1] if len(parts) > 1 else ""
    if not book_id.isdigit():
        return
    if action == "rv_list":
        kitob = Kitob.objects.filter(organization=bot.organization, pk=book_id).first()
        if not kitob:
            return _send(bot, chat_id, "Kitob topilmadi.")
        info = reviews.summary(kitob)
        reader = _reader(bot, telegram_id)
        markup = None
        if reader and reviews.has_read(reader, kitob):
            markup = _inline([[{"text": "✍️ Fikr qoldirish", "callback_data": f"rv_new:{kitob.pk}"}]])
        return _send(bot, chat_id, reviews.telegram_text(kitob, reviews.public_reviews(kitob), info), markup)
    kitob, reader = _review_book(bot, chat_id, telegram_id, book_id)
    if not kitob:
        return
    if action == "rv_new":
        return _send(
            bot, chat_id, reviews.RATE_PROMPT.format(title=telegram_escape(kitob.nomi)), reviews.rating_keyboard(kitob.pk)
        )
    rating = parts[2] if len(parts) > 2 else ""
    if not rating.isdigit() or not 1 <= int(rating) <= 5:
        return
    if action == "rv_rate":
        _set_session(bot, telegram_id, chat_id, "review_text", {"book": kitob.pk, "rating": int(rating)})
        return _send(
            bot, chat_id, reviews.TEXT_PROMPT.format(stars=reviews.stars(rating)), reviews.skip_keyboard(kitob.pk, rating)
        )
    if action == "rv_skip":
        _clear_session(bot, telegram_id)
        reviews.save_review(reader, kitob, rating)
        return _send(bot, chat_id, reviews.SAVED, _menu(bot, telegram_id))


def _review_text(bot, chat_id, telegram_id, sessiya, matn):
    _clear_session(bot, telegram_id)
    kitob, reader = _review_book(bot, chat_id, telegram_id, sessiya.data.get("book"))
    if not kitob:
        return
    reviews.save_review(reader, kitob, sessiya.data.get("rating", 5), matn)
    _send(bot, chat_id, reviews.SAVED, _menu(bot, telegram_id))


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
    except ValidationError as xato:
        _send(bot, chat_id, f"Band qilish mumkin emas: {_xato_matni(xato)}")
        return
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
        inv = f" ({berish.nusxa.inventar_raqami})" if berish.nusxa else ""
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
    # Ilgari faqat 10 ta (yarim API sahifasi) ko'rsatilardi. Endi API
    # PAGE_SIZE (20) dan boshlab, 200 tagacha bo'lgan barcha so'rovlar
    # sahifa-sahifa o'qiladi va kutubxonachiga yuboriladi.
    qs = (
        BandQilish.objects.filter(
            organization=bot.organization, holati="kutmoqda"
        )
        .select_related("kitob", "oquvchi")
        .order_by("so_rov_sanasi")[:BANDLAR_CHEKLAMI]
    )
    if not qs:
        return _send(bot, chat_id, "Kutilayotgan band so'rovlar yo'q.")
    for band in qs.iterator(chunk_size=BANDLAR_SAHIFA_O_LCHAMI):
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


def _band_qaror(bot, chat_id, telegram_id, band_id, tasdiq):
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
    except ValidationError as xato:
        _send(bot, chat_id, f"Amal bajarilmadi: {_xato_matni(xato)}")
    except Exception as xato:
        _send(bot, chat_id, f"Amal bajarilmadi: {telegram_escape(xato)}")


def _qaytarish(bot, chat_id, telegram_id, inventar):
    xodim = _staff(bot, telegram_id)
    if not xodim:
        return _send(bot, chat_id, "Bu amal faqat kutubxonachilar uchun.")
    from berish.models import Berish as BerishModel
    from berish.services import kitob_qaytar
    from nusxa.models import Nusxa

    nusxa = Nusxa.objects.filter(
        organization=bot.organization, inventar_raqami=inventar.strip().upper()
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
    except ValidationError as xato:
        return _send(bot, chat_id, f"Qaytarish xatosi: {_xato_matni(xato)}")
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
    membership, message = link_staff(bot.organization, kod, telegram_id)
    _send(bot, chat_id, message, _menu(bot, telegram_id) if membership else None)


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
        "/bekor — joriy amalni bekor qilish\n"
        "/qaytar — inventar raqami bilan kitob qaytarish (kutubxonachi)\n"
        "/ulash KOD — xodim Telegramini ulash (kutubxonachi)",
    )


def _text(bot, message):
    chat_id = message["chat"]["id"]
    telegram_id = message["from"]["id"]
    matn = (message.get("text") or "").strip()
    if not matn:
        return

    if message.get("via_bot"):
        # A book card posted from inline search: not a query, do not feed it to the search step.
        return

    sessiya = _session(bot, telegram_id)
    if sessiya and not matn.startswith("/"):
        if matn in MENYU_TUGMALARI:
            # Pastdagi tugma matn yuboradi — uni qidiruv so'zi yoki ariza
            # maydoni deb olish mumkin emas (aiogram'dagi himoyaga o'xshash).
            if matn == "ℹ️ Yordam":
                # Yordam hech qanday holatni buzmaydi; ariza bosqichi bo'lsa
                # yordamdan keyin savol qaytariladi.
                _yordam(bot, chat_id)
                savol = ARIZA_SAVOLLARI.get(sessiya.step)
                if savol:
                    _send(bot, chat_id, savol)
                return
            if sessiya.step.startswith(APPLICATION_STEP_PREFIXES):
                savol = ARIZA_SAVOLLARI.get(sessiya.step)
                if savol:
                    _send(
                        bot, chat_id,
                        f"{savol}\n\nAvval arizani tugating yoki /bekor bosing.",
                    )
                    return
            _clear_session(bot, telegram_id)
            # Tugma o'z bo'limiga quyidagi filtrlar orqali yetkaziladi.
        elif sessiya.step == "review_text":
            _review_text(bot, chat_id, telegram_id, sessiya, matn)
            return
        else:
            _ariza_text(bot, message, sessiya)
            return

    if matn.startswith("/start"):
        return _start(bot, message)
    if matn.startswith(("/bekor", "/cancel", "/start_over")):
        _clear_session(bot, telegram_id)
        return _send(
            bot,
            chat_id,
            "Bekor qilindi. Qayta urinish uchun /start bosing.",
            _menu(bot, telegram_id),
        )
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
    # Hujjatlarda `/qaytar` ham ishlatiladi — ikkala nom ham bir xil ish qiladi.
    if matn.startswith("/qaytar") or matn == "↩️ Qaytarish":
        if not _staff(bot, telegram_id):
            return _send(bot, chat_id, "Bu amal faqat kutubxonachilar uchun.")
        _set_session(bot, telegram_id, chat_id, "qaytarish")
        return _send(bot, chat_id, "Qaytarilayotgan nusxaning inventar raqamini kiriting:")
    if matn.startswith("/yordam") or matn == "ℹ️ Yordam":
        return _yordam(bot, chat_id)
    if matn == "🔎 Kitob qidirish":
        if bot.organization.has_capability("search_inline"):
            _clear_session(bot, telegram_id)
            return _send(
                bot, chat_id, "Kitob nomi, muallifi yoki ISBNi bo'yicha qidiring:",
                _inline([[{"text": "🔎 Qidirishni boshlash", "switch_inline_query_current_chat": ""}]]),
            )
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
    return _send(bot, chat_id, "Kerakli bo'limni tanlang.", _menu(bot, telegram_id))


def _callback_javob(bot, callback_id):
    """Inline tugma bosilganda Telegram'dagi aylanma indikatorni to'xtatadi."""
    if not callback_id:
        return
    try:
        answer_callback_query(bot.get_token(), callback_id)
    except Exception:
        # Xabar yuborilgan bo'lsa, spinner'ning qolishi foydalanuvchiga xalaqit
        # qilmaydi — lekin asosiy oqim buzilmasligi kerak.
        pass


def _callback(bot, callback):
    telegram_id = callback["from"]["id"]
    # Cards posted via inline search in other chats carry no `message`; reply in the user's private chat.
    chat_id = callback["message"]["chat"]["id"] if callback.get("message") else telegram_id
    data = callback.get("data", "")
    callback_id = callback.get("id")
    try:
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
            _kitob_karta(bot, chat_id, telegram_id, data.split(":", 1)[1])
        elif data.startswith("band_ok:"):
            _band_qaror(bot, chat_id, telegram_id, data.split(":", 1)[1], True)
        elif data.startswith("band_no:"):
            _band_qaror(bot, chat_id, telegram_id, data.split(":", 1)[1], False)
        elif data.startswith("band:"):
            _band_qilish(bot, chat_id, telegram_id, data.split(":", 1)[1])
        elif data.startswith("navbat:"):
            _navbatga_qosh(bot, chat_id, telegram_id, data.split(":", 1)[1])
        elif data.startswith("rv_"):
            _review_callback(bot, chat_id, telegram_id, data)
    finally:
        # `kitob:`/`band_ok:`/`band_no:` dan tashqari holatlar ham javobsiz
        # qolardi — shuning uchun javob bitta joyda, hamma holatda beriladi.
        _callback_javob(bot, callback_id)


def _is_link_command(message):
    text = (message.get("text") or "").strip()
    if text.startswith("/ulash"):
        return True
    parts = text.split(maxsplit=1)
    return parts[0].startswith("/start") and bool(code_from_start_payload(parts[1] if len(parts) > 1 else ""))


def _gate_message(bot, message):
    """Stop the update if the sender must first join the library's channel."""
    if message.get("via_bot") or message.get("chat", {}).get("type") not in (None, "private"):
        return False
    if _is_link_command(message):
        return False
    gate = subscription_gate(bot.organization, message["from"]["id"])
    if gate is None:
        return False
    _send(bot, message["chat"]["id"], gate_text(gate), gate_keyboard(gate))
    return True


def _gate_callback(bot, callback):
    telegram_id = callback["from"]["id"]
    data = callback.get("data", "")
    if data == CHECK_CALLBACK:
        gate = subscription_gate(bot.organization, telegram_id, fresh=True)
        if gate is not None:
            try:
                answer_callback_query(bot.get_token(), callback.get("id"), "Siz hali kanalga obuna bo'lmagansiz.")
            except Exception:
                pass
            return True
        _callback_javob(bot, callback.get("id"))
        _start(bot, {"chat": {"id": telegram_id}, "from": callback["from"], "text": "/start"})
        return True
    gate = subscription_gate(bot.organization, telegram_id)
    if gate is None:
        return False
    _callback_javob(bot, callback.get("id"))
    _send(bot, telegram_id, gate_text(gate), gate_keyboard(gate))
    return True


def handle_update(bot, update):
    if "message" in update:
        if _gate_message(bot, update["message"]):
            return True
        _text(bot, update["message"])
    elif "callback_query" in update:
        if _gate_callback(bot, update["callback_query"]):
            return True
        _callback(bot, update["callback_query"])
    elif "inline_query" in update:
        _inline_query(bot, update["inline_query"])
    return True
