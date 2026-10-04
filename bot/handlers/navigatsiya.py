"""Buyruqlar va menyu — DOIM birinchi bo'lib qayta ishlovchi router.

Nega alohida router:
    Boshqa handler'lar FSM state'iga (`Ariza.fish`, `Qidiruv.matn`) bog'langan
    va ular `main.py` da shu router'lardan keyin ro'yxatga olinadi. Agar
    menyu buyruqlari faqat shu handler'larda bo'lsa, foydalanuvchi ariza
    to'ldirayotganda /bekor yoki /yordam bossa, u matn "ism-familiya"
    sifatida qabul qilinardi (ba'zan esa ariza yuborilib ketardi) — va
    `/bekor` ham "ism-familiya" bo'lib ketardi.

    Shu sababli barcha buyruqlar (`/menu`, `/bekor`, `/qaytar`, bo'lim
    buyruqlari) shu router'da joylashtiriladi va `main.py` da BIRINCHI
    ro'yxatga olinadi. Bu yerda state tozalanadi, so'ng kerakli
    handler'ga murojaat qilinadi — oqimning o'z mantig'i o'z o'rnida
    saqlanadi.

Menyu endi chat ichidagi KATTA tugmalarda emas: standart Telegram «Menu»
tugmasi orqali ochiladi (`main.py::menyu_tugmasini_yoqish`), bo'limlar esa
`/menu` dan keyingi inline tugmalarda ko'rinadi.
"""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from handlers import kutubxonachi, qidiruv, shaxsiy, start
from keyboards import (
    ASOSIY_TUGMALAR,
    menyu_tugmalari,
    telefon_sorash,
)
from states import Ariza, KutubxonachiQaytarish, Qidiruv
from utils import yordam_matni

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
        "⚠️ Ariza to'ldirish yopildi (menyu ochildi).\n"
        "Qayta boshlash uchun /start buyrug'ini ishlating."
    )
    return True


async def _yordam_ber(message: Message, state: FSMContext) -> None:
    """`/yordam` — yozilayotgan ma'lumotni BUZMAYDI.

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
            + "\n\n<b>Sizning yozuingiz saqlanib qoldi</b> — quyidagi savolga "
            "javob bering:\n\n"
            f"{savol}",
            # Faqat telefon bosqichida kontakt tugmasi kerak — qolgan
            # hollarda pastdagi klaviatura bo'sh qoladi.
            reply_markup=(
                telefon_sorash() if joriy == Ariza.telefon.state else None
            ),
        )
        return

    await state.clear()
    await message.answer(yordam_matni(), reply_markup=menyu_tugmalari())


async def _menyuni_ochish(message: Message, state: FSMContext) -> None:
    """Menyu — barcha bo'limlarning inline tugmalari.

    Standart Telegram «Menu» tugmasi buyruqlar ro'yxatini ochadi; undan
    `/menu` tanlanganda shu oynaga chiroyli bo'lim menyusi ko'rinadi.
    """
    await _arizani_tugatish(message, state)
    await state.clear()
    await message.answer(
        "🏠 <b>Menyu</b>\n\nQuyidagi bo'limlardan birini tanlang "
        "(yoki /bekor bilan bekor qiling):",
        reply_markup=menyu_tugmalari(),
    )


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
    """Bot imkoniyatlarini tushuntiradi."""
    await _yordam_ber(message, state)


@router.message(Command("menu", "menyu", "bo'limlar"))
async def menyu_buyrugi(message: Message, state: FSMContext):
    """`/menu` — standart «Menu» tugmasidan keyingi bo'limlar menyusi."""
    await _menyuni_ochish(message, state)


# ------------------------------------------------------- bo'lim buyruqlari
# Standart «Menu» tugmasi orqali keladigan buyruqlar. Ularning matnlari
# `keyboards.bot_buyruglar()` ro'yxatiga mos kelishi kerak.
@router.message(Command("qidiruv", "qidrov"))
async def qidiruv_buyrugi(message: Message, state: FSMContext):
    await _arizani_tugatish(message, state)
    await state.clear()
    await qidiruv.qidiruv_boshla(message, state)


@router.message(Command("kategoriyalar", "kategoriya", "janrlar"))
async def kategoriyalar_buyrugi(message: Message, state: FSMContext):
    await _arizani_tugatish(message, state)
    await state.clear()
    await qidiruv.kategoriyalar(message)


@router.message(Command("kitoblarim", "mening_kitoblarim", "kitobim"))
async def kitoblarim_buyrugi(message: Message, state: FSMContext):
    await _arizani_tugatish(message, state)
    await state.clear()
    await shaxsiy.kitoblarim(message)


@router.message(Command("navbatlarim", "navbatim", "navbat"))
async def navbatlarim_buyrugi(message: Message, state: FSMContext):
    await _arizani_tugatish(message, state)
    await state.clear()
    await shaxsiy.navbatlarim(message)


@router.message(Command("bandlarim", "bandim", "bandlar_holati"))
async def bandlarim_buyrugi(message: Message, state: FSMContext):
    await _arizani_tugatish(message, state)
    await state.clear()
    await shaxsiy.bandlarim(message)


@router.message(Command("jarimalarim", "jarima", "jarimalar"))
async def jarimalarim_buyrugi(message: Message, state: FSMContext):
    await _arizani_tugatish(message, state)
    await state.clear()
    await shaxsiy.jarimalarim(message)


# ------------------------------------------------------- menyu: callback'lar
# Inline menyudagi bo'lim tugmalari — xabar ichida, maydon yonida emas.
# Har biri `Command` versiyasi bilan bir xil oqimni ishga tushiradi.
@router.callback_query(F.data.startswith("menyu:"))
async def menyu_bolimi(callback: CallbackQuery, state: FSMContext):
    """Menyu ichidagi bo'lim tugmasi."""
    if callback.message is None:
        await callback.answer("Xabar eskirgan. /menu yozing.", show_alert=True)
        return

    bolim = (callback.data or "").partition(":")[2]

    if bolim == "yordam":
        await _yordam_ber(callback.message, state)
        await callback.answer()
        return

    bolimlar = {
        "qidiruv": qidiruv.qidiruv_boshla,
        "kategoriya": qidiruv.kategoriyalar,
        "kitoblarim": shaxsiy.kitoblarim,
        "navbatlarim": shaxsiy.navbatlarim,
        "bandlarim": shaxsiy.bandlarim,
        "jarimalarim": shaxsiy.jarimalarim,
    }
    if bolim not in bolimlar:
        await callback.answer("Noma'lum bo'lim.", show_alert=True)
        return

    await _arizani_tugatish(callback.message, state)
    await state.clear()
    await bolimlar[bolim](callback.message, state)
    await callback.answer()


# Eski versiyalarda pastdiki katta tugmalardan yuborilgan matnlar —
# endi o'sha tugmalar yo'q, lekin eski xabar/eski klient qolgan bo'lishi
# mumkin. Bo'lim funksiyalari Command handler'lari bilan bir xil.
@router.message(F.text.in_(ASOSIY_TUGMALAR))
async def eski_tugma_matni(message: Message, state: FSMContext):
    """Eski katta tugma matni kelsa — menyu taklif qiladi."""
    await _arizani_tugatish(message, state)
    await state.clear()
    await message.answer(
        "ℹ️ Bu tugmalar endi ko'rsatilmaydi — menyu endi pastdagi standart "
        "«Menu» tugmasi orqali ochiladi.\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=menyu_tugmalari(),
    )