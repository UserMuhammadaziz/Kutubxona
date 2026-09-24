from datetime import datetime

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api_client import ApiXato, api
from keyboards import asosiy_menyu, otkazib_yuborish_tugmasi, telefon_sorash
from states import Ariza

router = Router(name="start")

KUTILMOQDA_XABAR = (
    "📋 A'zolik arizangiz ko'rib chiqilmoqda.\n\n"
    "Kutubxonachi tasdiqlagach, /start buyrug'ini qayta bosing va botdan "
    "foydalanishingiz mumkin."
)


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

    await state.set_state(Ariza.fish)
    await message.answer(
        "Assalomu alaykum! Kutubxona botidan foydalanish uchun avval a'zo "
        "bo'lishingiz kerak.\n\n"
        "Ism, familiyangizni kiriting:"
    )


@router.message(Ariza.fish)
async def ariza_fish(message: Message, state: FSMContext):
    fish = (message.text or "").strip()
    if not fish:
        await message.answer("Iltimos, ism-familiyangizni matn ko'rinishida yozing.")
        return

    await state.update_data(fish=fish)
    await state.set_state(Ariza.telefon)
    await message.answer(
        "Rahmat. Endi telefon raqamingizni yuboring:",
        reply_markup=telefon_sorash(),
    )


@router.message(Ariza.telefon, F.contact)
async def ariza_telefon(message: Message, state: FSMContext):
    data = await state.get_data()
    fish = data["fish"]
    telefon = message.contact.phone_number
    if not telefon.startswith("+"):
        telefon = f"+{telefon}"
    await state.update_data(telefon=telefon)
    await state.set_state(Ariza.tugilgan_sana)
    await message.answer(
        "Tug'ilgan sanangizni `YYYY-MM-DD` formatida kiriting (masalan: 2000-01-25):",
        reply_markup=otkazib_yuborish_tugmasi(),
    )


@router.message(Ariza.tugilgan_sana)
async def ariza_tugilgan_sana(message: Message, state: FSMContext):
    matn = (message.text or "").strip()
    if matn:
        try:
            sana = datetime.strptime(matn, "%Y-%m-%d").date()
        except ValueError:
            await message.answer(
                "Sana noto'g'ri formatda. `YYYY-MM-DD` ko'rinishida yozing (masalan: 2000-01-25) yoki "
                "⏭ O'tkazib yuborish tugmasini bosing.",
                reply_markup=otkazib_yuborish_tugmasi(),
            )
            return
        if sana > datetime.now().date():
            await message.answer(
                "Tug'ilgan sana kelajakda bo'lishi mumkin emas. Qayta kiriting:",
                reply_markup=otkazib_yuborish_tugmasi(),
            )
            return
        await state.update_data(tugilgan_sana=matn)
    else:
        await state.update_data(tugilgan_sana=None)

    await state.set_state(Ariza.manzil)
    await message.answer(
        "Manzilingizni yozing (ixtiyoriy):",
        reply_markup=otkazib_yuborish_tugmasi(),
    )


@router.message(Ariza.manzil)
async def ariza_manzil(message: Message, state: FSMContext):
    data = await state.get_data()
    manzil = (message.text or "").strip()
    await ariza_yuborish(message, state, data, manzil)


@router.callback_query(F.data == "ariza_skip")
async def ariza_skip(callback: CallbackQuery, state: FSMContext):
    holat = await state.get_state()
    if holat == Ariza.tugilgan_sana.state:
        await state.update_data(tugilgan_sana=None)
        await state.set_state(Ariza.manzil)
        await callback.message.answer(
            "Manzilingizni yozing (ixtiyoriy):",
            reply_markup=otkazib_yuborish_tugmasi(),
        )
    elif holat == Ariza.manzil.state:
        data = await state.get_data()
        await ariza_yuborish(callback.message, state, data, "")
    await callback.answer()


async def ariza_yuborish(message: Message, state: FSMContext, data: dict, manzil: str):
    fish = data["fish"]
    telefon = data["telefon"]
    tugilgan_sana = data.get("tugilgan_sana")
    telegram_id = message.from_user.id

    try:
        await api.ariza_yubor(
            telegram_id=telegram_id,
            fish=fish,
            telefon=telefon,
            tugilgan_sana=tugilgan_sana,
            manzil=manzil,
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
        "Kutubxonachi arizangizni tasdiqlagach, /start buyrug'ini bosing va "
        "botdan foydalanasiz."
    )


@router.message(Ariza.telefon)
async def ariza_telefon_notogri(message: Message):
    await message.answer("Iltimos, pastdagi tugma orqali telefon raqamingizni yuboring.")