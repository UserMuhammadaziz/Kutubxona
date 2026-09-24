from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

KITOB_QIDIRISH = "🔍 Kitob qidirish"
KATEGORIYALAR = "📚 Kategoriyalar"
MENING_KITOBLARIM = "📚 Mening kitoblarim"
NAVBATLARIM = "⏳ Navbatlarim"
JARIMALARIM = "💰 Jarimalarim"


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
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def otkazib_yuborish_tugmasi() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="ariza_skip")]]
    )


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