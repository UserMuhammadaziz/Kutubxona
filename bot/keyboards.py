from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

KITOB_QIDIRISH = "🔍 Kitob qidirish"
MENING_KITOBLARIM = "📚 Mening kitoblarim"
NAVBATLARIM = "⏳ Navbatlarim"
JARIMALARIM = "💰 Jarimalarim"


def asosiy_menyu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=KITOB_QIDIRISH)],
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


def kitob_batafsil_tugmasi(kitob_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ℹ️ Batafsil", callback_data=f"kitob:{kitob_id}")]
        ]
    )


def navbatga_turish_tugmasi(kitob_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕐 Navbatga turish", callback_data=f"navbat_tur:{kitob_id}")]
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