"""Buyruq va menyu tugmalari — DOIM birinchi bo'lib qayta ishlovchi router.

Nega alohida router:
    Boshqa handler'lar FSM state'iga (`Ariza.fish`, `Qidiruv.matn`) bog'langan
    va ular `main.py` da shu router'lardan keyin ro'yxatga olinadi. Agar
    menyu tugmalari faqat shu handler'larda bo'lsa, foydalanuvchi ariza
    to'ldirayotganda "📚 Kategoriyalar" bossa, u matn "sinf" yoki "fish"
    sifatida qabul qilinardi (ba'zan esa ariza yuborilib ketardi) — va
    `/bekor` ham "ism-familiya" bo'lib ketardi.

    Shu sababli barcha buyruqlar (`/bekor`, `/qaytar`) va pastdagi menyu
    tugmalari shu router'da joylashtiriladi va `main.py` da BIRINCHI
    ro'yxatga olinadi. Bu yerda state tozalanadi, so'ng kerakli
    handler'ga murojaat qilinadi — oqimning o'z mantig'i o'z o'rnida
    saqlanadi.
"""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from handlers import kutubxonachi, qidiruv, shaxsiy, start
from keyboards import (
    JARIMALARIM,
    KATEGORIYALAR,
    KITOB_QIDIRISH,
    MENING_KITOBLARIM,
    NAVBATLARIM,
)
from states import Ariza

router = Router(name="navigatsiya")

ARIZA_BOSQICHLARI = frozenset(Ariza.__all_states__)


async def _arizani_tugatish(message: Message, state: FSMContext) -> bool:
    """Ariza bosqichida bo'lsa — ogohlantirib, state'ni tozalaydi.

    Qaytaradi: ariza bekor qilindi (True) yoki ariza bosqichida
    emas edi (False).
    """
    joriy = await state.get_state()
    if joriy not in ARIZA_BOSQICHLARI:
        return False
    await state.clear()
    await message.answer(
        "⚠️ Ariza to'ldirish yopildi (menyu tugmasi bosildi).\n"
        "Qayta boshlash uchun /start bosing."
    )
    return True


# ---------------------------------------------------------------- buyruqlar
@router.message(Command("bekor", "start_over", "cancel"))
async def bekor(message: Message, state: FSMContext):
    """Ariza yoki qidiruvni bekor qiladi va state'ni tozalaydi."""
    await start.ariza_bekor_qilish(message, state)


@router.message(Command("qaytar"))
async def qaytar(message: Message, state: FSMContext):
    """Kitob qaytarishni kutubxonachilar uchun boshlaydi.

    `state.set_state()` o'z-o'zidan avvalgi state'ni almashtiradi, shuning
    uchun ariza bosqichi ham to'g'ri to'xtaydi.
    """
    await kutubxonachi.qaytarish_boshla(message, state)


# ------------------------------------------------------------------- menyu
@router.message(F.text == KITOB_QIDIRISH)
async def menyu_qidirish(message: Message, state: FSMContext):
    await _arizani_tugatish(message, state)
    await state.clear()
    await qidiruv.qidiruv_boshla(message, state)


@router.message(F.text == KATEGORIYALAR)
async def menyu_kategoriya(message: Message, state: FSMContext):
    await _arizani_tugatish(message, state)
    await state.clear()
    await qidiruv.kategoriyalar(message)


@router.message(F.text == MENING_KITOBLARIM)
async def menyu_kitoblarim(message: Message, state: FSMContext):
    await _arizani_tugatish(message, state)
    await state.clear()
    await shaxsiy.kitoblarim(message)


@router.message(F.text == NAVBATLARIM)
async def menyu_navbatlarim(message: Message, state: FSMContext):
    await _arizani_tugatish(message, state)
    await state.clear()
    await shaxsiy.navbatlarim(message)


@router.message(F.text == JARIMALARIM)
async def menyu_jarimalarim(message: Message, state: FSMContext):
    await _arizani_tugatish(message, state)
    await state.clear()
    await shaxsiy.jarimalarim(message)