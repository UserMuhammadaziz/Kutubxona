from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from api_client import ApiXato, api
from keyboards import (
    asosiy_menyu,
    klaviatura_olib_tashla,
    matndan_telefon_keltirish,
    telefon_keltirish,
    telefon_sorash,
)
from states import Ariza

router = Router(name="start")

KUTILMOQDA_XABAR = (
    "📋 A'zolik arizangiz ko'rib chiqilmoqda.\n\n"
    "Kutubxonachi tasdiqlagach, /start buyrug'ini qayta bosing va botdan "
    "foydalanishingiz mumkin."
)

SINF_MASALALARI = "7-A, 9-B, 10-"


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id

    # Bog'langanmi? Oquvchi topilmasa 404 "topilmadi" qaytaradi.
    try:
        await api.kitoblarim(telegram_id)
        await message.answer(
            "Yana xush kelibsiz! 📚 Kerakli bo'limni tanlang:",
            reply_markup=asosiy_menyu(),
        )
        return
    except ApiXato as e:
        if e.kod != "topilmadi":
            await message.answer(f"Xatolik yuz berdi: {e.detail}")
            return

    # Bog'lanmagan — ariza holatini tekshiramiz.
    try:
        holat = await api.ariza_holati(telegram_id)
    except ApiXato as e:
        await message.answer(f"Xatolik yuz berdi: {e.detail}")
        return

    if holat.get("holati") == "kutmoqda":
        await message.answer(KUTILMOQDA_XABAR)
        return

    if holat.get("holati") == "bekor":
        izoh = holat.get("izoh") or "Sabab ko'rsatilmagan"
        await message.answer(
            "❌ Oldingi arizangiz rad etilgan.\n"
            f"📝 Sabab: {izoh}\n\n"
            "Qayta urinib ko'rishni xohlaysizmi?"
        )

    await _arizaga_kirish(message, state)


async def _arizaga_kirish(message: Message, state: FSMContext):
    await state.set_state(Ariza.fish)
    await message.answer(
        "Assalomu alaykum! Kutubxona botidan foydalanish uchun avval a'zo "
        "bo'lishingiz kerak.\n\n"
        "Ro'yxatga olish uchun 3 ta ma'lumot kerak:\n"
        "1️⃣ Ism-familiyangiz\n"
        "2️⃣ Telefon raqamingiz\n"
        "3️⃣ Sinfingiz\n\n"
        "1️⃣ Ism-familiyangizni yozing:"
    )


@router.message(Ariza.fish)
async def ariza_fish(message: Message, state: FSMContext):
    fish = (message.text or "").strip()
    if not fish:
        await message.answer("Iltimos, ism-familiyangizni matn ko'rinishida yozing.")
        return
    if len(fish) > 130:
        await message.answer("Ism-familiya juda uzun (maksimum 130 belgi). Qayta yozing:")
        return

    await state.update_data(fish=fish)
    await state.set_state(Ariza.telefon)
    await message.answer(
        "2️⃣ Rahmat. Endi telefon raqamingizni yuboring:",
        reply_markup=telefon_sorash(),
    )


@router.message(Ariza.telefon, F.contact)
async def ariza_telefon(message: Message, state: FSMContext):
    contact = message.contact

    # Telegram Contact boshqa akkauntga tegishli bo'lishi mumkin (kontakt
    # sifatida tanlangan). O'z raqamini tasdiqlashi uchun user_id mos bo'lishi
    # kerak.
    if contact.user_id and contact.user_id != message.from_user.id:
        await message.answer(
            "⚠️ Bu kontakt sizning akkauntingizga tegishli emas. "
            "O'z telefon raqamingizni Telegram kontaktlaridan yuboring "
            "(yoki raqamni qo'lda yozib bo'lishingiz mumkin):"
        )
        return

    telefon = telefon_keltirish(contact.phone_number)
    if not telefon:
        await message.answer(
            "❌ Telefon raqam +998901234567 formatida bo'lishi kerak.\n\n"
            "Quyidagilar to'g'ri keladi: +998901234567, +998 90 123 45 67.\n"
            "📱 Pastdagi tugma orqali qayta yuboring:"
        )
        return

    await _telefon_qabul(message, state, telefon)


@router.message(Ariza.telefon)
async def ariza_telefon_matn(message: Message, state: FSMContext):
    """Tugmani bosmasdan, raqamni oddiy matn ko'rinishida yuborish."""
    telefon = matndan_telefon_keltirish(message.text or "")
    if not telefon:
        await message.answer(
            "Iltimos, pastdagi tugma orqali telefon raqamingizni yuboring.\n"
            "Yoki raqamni qo'lda yozib bo'lishingiz mumkin "
            "(masalan: +998901234567)"
        )
        return

    await _telefon_qabul(message, state, telefon)


async def _telefon_qabul(message: Message, state: FSMContext, telefon: str):
    """Raqamni saqlaydi, telefon klaviaturasini olib tashlaydi va keyingi bosqichga o'tadi."""
    await state.update_data(telefon=telefon)
    await state.set_state(Ariza.sinf)
    await message.answer(
        f"✅ Telefon raqamingiz muvaffaqiyatli tasdiqlandi: {telefon}\n\n"
        f"3️⃣ Endi sinfingizni yozing (masalan: {SINF_MASALALARI}):",
        reply_markup=klaviatura_olib_tashla(),
    )


@router.message(Ariza.sinf)
async def ariza_sinf(message: Message, state: FSMContext):
    sinf = (message.text or "").strip()
    if not sinf:
        await message.answer(
            f"Iltimos, sinfingizni yozing (masalan: {SINF_MASALALARI}):"
        )
        return
    if len(sinf) > 30:
        await message.answer("Sinf nomi juda uzun (maksimum 30 belgi). Qayta yozing:")
        return

    data = await state.get_data()
    await _arizani_yuborish(message, state, data, sinf)


async def _arizani_yuborish(message: Message, state: FSMContext, data: dict, sinf: str):
    telegram_id = message.from_user.id
    try:
        await api.ariza_yubor(
            telegram_id=telegram_id,
            fish=data["fish"],
            telefon=data["telefon"],
            sinf=sinf,
        )
    except ApiXato as e:
        await state.clear()
        xabarlar = {
            "allaqachon_azo": "Siz allaqachon ro'yxatdan o'tgansiz. /start bosing.",
            "ariza_kutmoqda": KUTILMOQDA_XABAR,
            "notogri_telefon": "Telefon raqam formati noto'g'ri. Qaytadan urinib ko'ring.",
        }
        await message.answer(xabarlar.get(e.kod, f"Xatolik: {e.detail}"))
        return

    await state.clear()
    await message.answer(
        "✅ Arizangiz yuborildi!\n\n"
        f"📋 Ism: {data['fish']}\n"
        f"📞 Telefon: {data['telefon']}\n"
        f"🎓 Sinf: {sinf}\n\n"
        "Kutubxonachi arizangizni tasdiqlagach, /start buyrug'ini bosing va "
        "botdan foydalanasiz. Tasdiqlash yoki rad etish natijasi shu yerga "
        "xabar qilinadi."
    )
