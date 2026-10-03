import re

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

KITOB_QIDIRISH = "🔍 Kitob qidirish"
KATEGORIYALAR = "📚 Kategoriyalar"
MENING_KITOBLARIM = "📚 Mening kitoblarim"
NAVBATLARIM = "⏳ Navbatlarim"
JARIMALARIM = "💰 Jarimalarim"
TELEFON_YUBORISH = "📱 Telefon raqamni yuborish"

# Asosiy menyudagi barcha tugma matnlari. Ariza to'ldirilayotgan paytda
# foydalanuvchi shu tugmalardan birini bossa, matn "sinf" yoki "kasb"
# sifatida yuborilmasligi kerak — shuning uchun handler'lar ro'yxatdan
# foydalanadi (`start.py::_menyu_tugmasi_bosilganmi`).
ASOSIY_TUGMALAR = frozenset(
    {KITOB_QIDIRISH, KATEGORIYALAR, MENING_KITOBLARIM, NAVBATLARIM, JARIMALARIM}
)


def asosiy_menyu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=KITOB_QIDIRISH), KeyboardButton(text=KATEGORIYALAR)],
            [KeyboardButton(text=MENING_KITOBLARIM), KeyboardButton(text=NAVBATLARIM)],
            [KeyboardButton(text=JARIMALARIM)],
        ],
        resize_keyboard=True,
    )


def telefon_sorash() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=TELEFON_YUBORISH, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def klaviatura_olib_tashla() -> ReplyKeyboardRemove:
    """Telefon raqami qabul qilingach pastdagi tugmalarni yo'q qiladi."""
    return ReplyKeyboardRemove()


# ---------- A'rolik arizasi ----------

ARIZA_ROL_OQUVCHI = "oquvchi"
ARIZA_ROL_OQITUVCHI = "oqituvchi"

ARIZA_ROL_TUGMA_MATNLARI = {
    ARIZA_ROL_OQUVCHI: "🎓 Oquvchi sifatida a'riza yuborish",
    ARIZA_ROL_OQITUVCHI: "👨‍🏫 O'qituvchi sifatida a'riza yuborish",
}


def ariza_rol_tugmalari() -> InlineKeyboardMarkup:
    """/start da ariza yuboruvchi rolini tanlaydigan inline tugmalar."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ARIZA_ROL_TUGMA_MATNLARI[ARIZA_ROL_OQUVCHI],
                    callback_data=f"ariza_rol:{ARIZA_ROL_OQUVCHI}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=ARIZA_ROL_TUGMA_MATNLARI[ARIZA_ROL_OQITUVCHI],
                    callback_data=f"ariza_rol:{ARIZA_ROL_OQITUVCHI}",
                )
            ],
        ]
    )


def telefon_keltirish(raw: str) -> str | None:
    """Raqamni `+998XXXXXXXXX` ko'rinishiga keltiradi, imkonsiz bo'lsa None.

    Qabul qilinadigan yozuvlar: `+998901234567`, `998901234567`,
    `+998 90 123 45 67`, `+998-90-123-45-67`, `00998901234567`, `901234567` (998 yozilmasdan).
    Bo'sh joy, chiziqcha va qavs ( ) olib tashlanadi.
    """
    if not raw:
        return None
    raqamlar = re.sub(r"\D", "", raw)
    if raqamlar.startswith("00998"):
        raqamlar = "998" + raqamlar[5:]
    if raqamlar.startswith("998"):
        yakuniy = "+" + raqamlar
    elif raqamlar.startswith("9") and len(raqamlar) == 9:
        # Raqam 998 yozilmasdan kelgan bo'lsa (masalan "901234567").
        yakuniy = "+998" + raqamlar
    else:
        return None
    # "+998" (4 belgi) + 9 ta raqam = 13 belgi — backend validatori bilan bir xil.
    return yakuniy if re.fullmatch(r"\+998\d{9}", yakuniy) else None


def matndan_telefon_keltirish(text: str) -> str | None:
    """Matn ichidan telefon raqamini ajratib oladi (asosiy usul Telegram Contact)."""
    if not text or TELEFON_YUBORISH in text:
        return None
    for candidat in re.findall(r"\+?\d[\d\s\-()]{6,}", text):
        telefon = telefon_keltirish(candidat)
        if telefon:
            return telefon
    return None


def kitob_batafsil_tugmasi(kitob_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ℹ️ Batafsil", callback_data=f"kitob:{kitob_id}")]
        ]
    )


def janr_tugmalari(janrlar: list[dict], qator_soni: int = 2) -> InlineKeyboardMarkup:
    """Janrlar bo'yicha inline tugmalar (qatorida qator_soni dan tugma)."""
    tugmalar = [
        InlineKeyboardButton(
            text=f"📖 {j['label']} ({j['soni']})",
            callback_data=f"janr:{j['key']}",
        )
        for j in janrlar
    ]
    qatorlar = [
        tugmalar[i : i + qator_soni] for i in range(0, len(tugmalar), qator_soni)
    ]
    return InlineKeyboardMarkup(inline_keyboard=qatorlar)


JANR_ORQAGA = "🔙 Janrlar"


def janr_kitob_tugmalari(
    janr: str,
    kitoblar: list[dict],
    sahifa: int,
    jami: int,
    qator_soni: int = 1,
    qatorlar_soni: int = 10,
) -> InlineKeyboardMarkup:
    """Tanlangan janrdagi kitoblar: bittadan (qator_soni=1), bo'yiga qatorlar_soni
    (10) tasi — bitta ekranda 10 tagacha kitob nomi inline tugma, nomi to'liq
    ko'rinadi. Yoniga o'tish (◀️ Oldingi / Keyingi ▶️) tugmalari orqali janrdagi
    hamma kitobni varaqlash mumkin (jami jami ta)."""

    ko_rsatiladi = kitoblar[: qator_soni * qatorlar_soni]
    tugmachalar = []
    for k in ko_rsatiladi:
        nomi = k["nomi"]
        matn = nomi if len(nomi) <= 60 else f"{nomi[:59]}…"
        tugmachalar.append(
            InlineKeyboardButton(
                text=f"📖 {matn}",
                callback_data=f"jbook:{janr}:{sahifa}:{k['id']}",
            )
        )

    qatorlar = [
        tugmachalar[i : i + qator_soni]
        for i in range(0, len(tugmachalar), qator_soni)
    ]

    jami_sahifalar = max(1, -(-jami // (qator_soni * qatorlar_soni)))
    nav = []
    if sahifa > 1:
        nav.append(
            InlineKeyboardButton(
                text="◀️ Oldingi", callback_data=f"jpage:{janr}:{sahifa - 1}"
            )
        )
    nav.append(
        InlineKeyboardButton(text=f"{sahifa} / {jami_sahifalar}", callback_data="jpage:bosh")
    )
    if sahifa < jami_sahifalar:
        nav.append(
            InlineKeyboardButton(
                text="Keyingi ▶️", callback_data=f"jpage:{janr}:{sahifa + 1}"
            )
        )
    qatorlar.append(nav)
    qatorlar.append([InlineKeyboardButton(text=JANR_ORQAGA, callback_data="janrlar")])
    return InlineKeyboardMarkup(inline_keyboard=qatorlar)


def kitob_band_qilish_tugmalari(kitob_id: int, qaytish: str | None = None) -> InlineKeyboardMarkup:
    """Batafsil sahifada: kitobni band qilish + (berilgan bo'lsa) ro'yxatga qaytish."""
    inline_keyboard = [
        [InlineKeyboardButton(text="🕐 Band qilish", callback_data=f"navbat_tur:{kitob_id}")]
    ]
    if qaytish:
        inline_keyboard.append(
            [InlineKeyboardButton(text="🔙 Ro'yxatga qaytish", callback_data=qaytish)]
        )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def navbatga_turish_tugmasi(kitob_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕐 Band qilish", callback_data=f"navbat_tur:{kitob_id}")]
        ]
    )


def taklif_javob_tugmalari(navbat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Olaman", callback_data=f"navbat_javob:{navbat_id}:olaman"),
                InlineKeyboardButton(text="❌ Kerak emas", callback_data=f"navbat_javob:{navbat_id}:kerak_emas"),
            ]
        ]
    )


def navbatdan_chiqish_tugmasi(navbat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚪 Navbatdan chiqish", callback_data=f"navbat_chiq:{navbat_id}")]
        ]
    )


def qaytarish_tasdiq_tugmasi(berish_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Qaytarib olish", callback_data=f"qaytar:{berish_id}")]
        ]
    )