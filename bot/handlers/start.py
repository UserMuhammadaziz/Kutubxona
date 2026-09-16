from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from api_client import ApiXato, api
from keyboards import asosiy_menyu, telefon_sorash
from states import BogClash

router = Router(name="start")


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id

    # /api/readers/ ro'yxati IsLibrarian talab qiladi, shuning uchun
    # "bog'langanmi?" tekshiruvini ochiq /api/loans/my/ orqali qilamiz:
    # 404 "topilmadi" — bog'lanmagan, aks holda (bo'sh ro'yxat bo'lsa ham) bog'langan.
    try:
        await api.kitoblarim(telegram_id)
        await message.answer(
            "Yana xush kelibsiz! 📚 Kerakli bo'limni tanlang:",
            reply_markup=asosiy_menyu(),
        )
    except ApiXato as e:
        if e.kod == "topilmadi":
            await state.set_state(BogClash.karta)
            await message.answer(
                "Assalomu alaykum! Kutubxona botiga xush kelibsiz.\n\n"
                "Kutubxona kartangiz raqamini kiriting (masalan: LIB-2026-0417):"
            )
        else:
            await message.answer(f"Xatolik yuz berdi: {e.detail}")


@router.message(BogClash.karta)
async def karta_qabul(message: Message, state: FSMContext):
    karta = (message.text or "").strip().upper()
    if not karta:
        await message.answer("Iltimos, karta raqamini matn ko'rinishida yuboring.")
        return

    await state.update_data(karta_raqami=karta)
    await state.set_state(BogClash.telefon)
    await message.answer(
        "Rahmat. Endi telefon raqamingizni yuboring:",
        reply_markup=telefon_sorash(),
    )


@router.message(BogClash.telefon, F.contact)
async def telefon_qabul(message: Message, state: FSMContext):
    data = await state.get_data()
    karta = data["karta_raqami"]
    telefon = message.contact.phone_number
    if not telefon.startswith("+"):
        telefon = f"+{telefon}"
    telegram_id = message.from_user.id

    try:
        await api.bind(telefon=telefon, karta_raqami=karta, telegram_id=telegram_id)
    except ApiXato as e:
        await state.clear()
        if e.kod == "topilmadi":
            await message.answer(
                "Ma'lumot topilmadi, kutubxonachiga murojaat qiling.",
            )
        elif e.kod == "band":
            await message.answer("Bu telegram akkaunt boshqa o'quvchiga bog'langan.")
        else:
            await message.answer(f"Xatolik: {e.detail}")
        return

    await state.clear()
    await message.answer(
        "✅ Karta muvaffaqiyatli bog'landi!\n\nKerakli bo'limni tanlang:",
        reply_markup=asosiy_menyu(),
    )


@router.message(BogClash.telefon)
async def telefon_notogri(message: Message):
    await message.answer("Iltimos, pastdagi tugma orqali telefon raqamingizni yuboring.")
    