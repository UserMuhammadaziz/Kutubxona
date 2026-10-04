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
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from handlers import kutubxonachi, qidiruv, shaxsiy, start
from keyboards import (
    BANDLARIM,
    BOSHLASH,
    JARIMALARIM,
    KATEGORIYALAR,
    KITOB_QIDIRISH,
    MENING_KITOBLARIM,
    MENYU,
    MENYU_YORDAM,
    NAVBATLARIM,
    YORDAM,
    ariza_klaviaturasi,
    menyu_tugmalari,
)
from states import Ariza, KutubxonachiQaytarish, Qidiruv
from utils import x, xabarni_tahrirlash, yordam_matni

router = Router(name="navigatsiya")

ARIZA_BOSQICHLARI = frozenset(Ariza.__all_states__)
# Foydalanuvchi matn yozayotgan barcha holatlar. Shu holatlarda yordam
# so'ralsa, ariza/kiritish bekor qilinmaydi — yordam ko'rsatilib, savol
# o'sha yerga qaytariladi.
YOZISH_BOSQICHLARI = ARIZA_BOSQICHLARI | {
    Qidiruv.matn.state,
    KutubxonachiQaytarish.inventar.state,
}


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


async def _yordam_ber(message: Message, state: FSMContext) -> None:
    """«❓ Yordam» yoki `/yordam` — yozilayotgan ma'lumotni BUZMAYDI.

    Ariza to'ldirilayotganda yordam so'ralsa, ariza bekor qilinardi —
    foydalanuvchi bir necha maydon to'ldirib, yordam ko'rmoqchi bo'lganda
    hammasi yo'qolardi. Endi yordam ko'rsatiladi va aynan shu savol
    qaytariladi, shuning uchun foydalanuvchi o'z joyida davom eta oladi.
    """
    joriy = await state.get_state()

    if joriy in YOZISH_BOSQICHLARI:
        if joriy == Qidiruv.matn.state:
            savol = qidiruv.QIDIRUV_SAVOLI
        elif joriy == KutubxonachiQaytarish.inventar.state:
            savol = kutubxonachi.INVENTAR_SAVOLI
        else:
            savol = start.joriy_savol(joriy, await state.get_data())
        await message.answer(
            yordam_matni()
            + "\n\n<b>Sizning yozumingiz saqlanib qoldi</b> — quyidagi savolga "
            "javob bering:\n\n"
            f"{savol}",
            reply_markup=ariza_klaviaturasi(
                telefon_tugmasi=joriy == Ariza.telefon.state
            ),
        )
        return

    await state.clear()
    await message.answer(yordam_matni(), reply_markup=menyu_tugmalari())


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


@router.message(Command("bandlar", "band"))
async def bandlar_kutubxonachi(message: Message, state: FSMContext):
    """Kutubxonachi uchun band so'rovlari ro'yxati (tasdiqlash/rad etish)."""
    await kutubxonachi.bandlar_koritaz(message, state)


@router.message(Command("yordam", "help", "yordamcha"))
async def yordam_buyrugi(message: Message, state: FSMContext):
    """Bot imkoniyatlarini tushuntiradi (inline «❓ Yordam» bilan bir xil)."""
    await _yordam_ber(message, state)


# ------------------------------------------------------------------- menyu
@router.message(F.text == BOSHLASH)
async def boshlash_tugmasi(message: Message, state: FSMContext):
    """«▶️ Boshlash» — ariza maydoni yonidagi tugma.

    `/start` bilan bir xil: state tozalanadi va oqim qayta boshlanadi.
    """
    await state.clear()
    await start.start(message)


@router.message(F.text == MENYU)
async def menyu_tugmasi(message: Message, state: FSMContext):
    """«🏠 Menyu» — uning ichida Start va Yordam."""
    await _arizani_tugatish(message, state)
    await state.clear()
    await message.answer(
        "🏠 <b>Menyu</b>\n\nQuyidagi bo'limlardan birini tanlang:",
        reply_markup=menyu_tugmalari(),
    )


@router.callback_query(F.data == "menyu:start")
async def menyu_start(callback: CallbackQuery):
    """Menyu ichidagi «▶️ Start» — /start bilan bir xil oqimni ishga tushiradi."""
    if callback.message is None:
        await callback.answer("Xabar eskirgan. /start yozing.", show_alert=True)
        return

    await start.start(callback.message)
    await callback.answer()


@router.callback_query(F.data == "menyu:yordam")
async def menyu_yordam(callback: CallbackQuery):
    """Menyu ichidagi «❓ Yordam»."""
    if callback.message is None:
        await callback.answer("Xabar eskirgan. /yordam yozing.", show_alert=True)
        return

    await xabarni_tahrirlash(callback, yordam_matni(), reply_markup=menyu_tugmalari())
    await callback.answer()


@router.message(F.text.in_({MENYU_YORDAM, YORDAM, "Yordam", "/yordam"}))
async def menyu_yordam_tugmasi(message: Message, state: FSMContext):
    await _yordam_ber(message, state)


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


@router.message(F.text == BANDLARIM)
async def menyu_bandlarim(message: Message, state: FSMContext):
    await _arizani_tugatish(message, state)
    await state.clear()
    await shaxsiy.bandlarim(message)