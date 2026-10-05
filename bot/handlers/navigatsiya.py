"""Buyruqlar va menyu — DOIM birinchi bo'lib qayta ishlovchi router.

Nega alohida router:
    Boshqa handler'lar FSM state'iga (`Ariza.fish`, `Qidiruv.matn`) bog'langan
    va ular `main.py` da shu router'lardan keyin ro'yxatga olinadi. Agar
    menyu buyruqlari faqat shu handler'larda bo'lsa, foydalanuvchi ariza
    to'ldirayotganda /bekor yoki /yordam bossa, u matn "ism-familiya"
    sifatida qabul qilinardi (ba'zan esa ariza yuborilib ketardi) — va
    `/bekor` ham "ism-familiya" bo'lib ketardi.

    Shu sababli barcha buyruqlar (`/bekor`, `/qaytar`, bo'lim buyruqlari)
    shu router'da joylashtiriladi va `main.py` da BIRINCHI ro'yxatga
    olinadi. Bu yerda state tozalanadi, so'ng kerakli handler'ga murojaat
    qilinadi — oqimning o'z mantig'i o'z o'rnida saqlanadi.

Menyu tuzilishi:
    * Bo'limlar — xabar yozish maydonining OSTIDAGI katta tugmalar
      (`keyboards.asosiy_tugmalar_klaviaturasi`). Ular matn yuboradi, shuning
      uchun `qidiruv.py` / `shaxsiy.py` dagi `F.text == ...` filtrlari
      ushlaydi. Bu router'da ularga **qarshi umumiy filtr yo'q** — aks holda
      bu router birinchi bo'lib turgani uchun barcha tugmalar yutilib,
      hech qanday bo'lim ishlamay qolardi.
    * `/yordam` — ham pastdagi tugma, ham standart «Menu» buyrug'i.
"""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from handlers import kutubxonachi, qidiruv, shaxsiy, start
from keyboards import (
    MENYU_YORDAM,
    asosiy_tugmalar_klaviaturasi,
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

        if joriy == Ariza.telefon.state:
            # Telefon bosqichida kontakt tugmasi kerak.
            klaviatura = telefon_sorash()
        elif joriy in ARIZA_BOSQICHLARI:
            # Ariza maydonlarida (ism, sinf, kasb) bo'lim tugmalari kerak
            # emas: ular matn yuboradi va maydonga tushib, arizani behuda
            # qilardi. `start.py` o'z himoyasini qiladi, lekin klaviatura
            # ko'rinmasligi ham to'g'ri — foydalanuvchi faqat savolga
            # javob yozadi.
            klaviatura = None
        else:
            # Qidiruv/inventar maydonida bo'lim tugmalari foydali: yangi
            # bo'limga o'tish arizani bekor qilmaydi (`_arizani_tugatish`
            # faqat ARIZA bosqichlariga taalluq).
            klaviatura = asosiy_tugmalar_klaviaturasi()

        await message.answer(
            yordam_matni()
            + "\n\n<b>Sizning yozuingiz saqlanib qoldi</b> — quyidagi savolga "
            "javob bering:\n\n"
            f"{savol}",
            reply_markup=klaviatura,
        )
        return

    await state.clear()
    await message.answer(yordam_matni(), reply_markup=asosiy_tugmalar_klaviaturasi())


async def _menyuni_ochish(message: Message, state: FSMContext) -> None:
    """Menyu — pastdigi katta tugmalarni ko'rsatadi.

    Bo'limlar endi inline emas, pastdagi klaviatura bo'lib chiqadi: ular
    eng tez-tez bosiladigan joyda turishi kerak (bosilganda matn keladi,
    `qidiruv.py` / `shaxsiy.py` filtrlari ushlaydi).
    """
    await _arizani_tugatish(message, state)
    await state.clear()
    await message.answer(
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=asosiy_tugmalar_klaviaturasi(),
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
    """`/menu` — pastdigi bo'lim tugmalarini ko'rsatadi.

    `/menu` «Menu» tugmasi ro'yxatiga qo'yilmaydi (u yerda faqat `/start` va
    `/yordam` bor), lekin qo'lda yozilishi va eski xabarlardagi havolalar
    uchun ishlayveradi.
    """
    await _menyuni_ochish(message, state)


# ------------------------------------------------------- bo'lim buyruqlari
# Bo'limlarning buyruq ko'rinishi. Pastdagi klaviatura tugmalari ham shu
# funksiyalarni ishga tushiradi (matn keladi -> `F.text == ...` filtrlari),
# shuning uchun bu yerdagi handler'lar buyruq bilan kelganda ham, tugma
# bilan kelganda ham bir xil natija beradi.
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
# Eski xabarlardagi inline menyu tugmalari. Ularga endi yangi tugma qo'shilmaydi
# (bo'limlar pastdagi klaviaturada), lekin eski xabarda qolgan tugmalar
# ishlashida davom etadi — aks holda "eskirgan" degan xato chiqardi.
@router.callback_query(F.data.startswith("menyu:"))
async def menyu_bolimi(callback: CallbackQuery, state: FSMContext):
    """Menyu ichidagi bo'lim tugmasi."""
    if callback.message is None:
        await callback.answer("Xabar eskirgan. /start yozing.", show_alert=True)
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


# ------------------------------------------------------- pastdagi «Yordam»
# Bu router `main.py` da BIRRINCHI ro'yxatga olindi. Shu sababli bu yerda
# faqat `/yordam` buyrug'iga tegishli filtr qo'yiladi.
#
# ESKI `F.text.in_(ASOSIY_TUGMALAR)` filtri SHU YERDA turardi va u barcha
# bo'lim tugmalarini yutib qo'yardi: foydalanuvchi "Kitob qidirish"ni b bosgan
# taqdirda ham faqat menyu qaytib kelardi — hech qanday bo'lim ishlamaydi.
# Bo'lim tugmalari endi pastdagi klaviatura orqali ishlaydi va ularni
# `qidiruv.py` / `shaxsiy.py` dagi `F.text == ...` filtrlari ushlaydi.
@router.message(F.text == MENYU_YORDAM)
async def yordam_tugmasi(message: Message, state: FSMContext):
    """Pastdagi «❓ Yordam» tugmasi — `/yordam` bilan bir xil ish qiladi."""
    await _yordam_ber(message, state)