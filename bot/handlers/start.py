import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api_client import ApiXato, api
from keyboards import (
    ARIZA_ROL_OQITUVCHI,
    ARIZA_ROL_OQUVCHI,
    ASOSIY_TUGMALAR,
    ariza_rol_tugmalari,
    klaviatura_olib_tashla,
    matndan_telefon_keltirish,
    menyu_tugmalari,
    telefon_keltirish,
    telefon_sorash,
)
from states import Ariza
from utils import x, xabarni_tahrirlash

router = Router(name="start")
logger = logging.getLogger(__name__)

KUTILMOQDA_XABAR = (
    "📋 A'zolik arizangiz ko'rib chiqilmoqda.\n\n"
    "Kutubxonachi tasdiqlagach, /start buyrug'ini qayta bosing va botdan "
    "foydalanishingiz mumkin."
)

SINF_MASALALARI = "7-A, 9-B, 10-"
KASB_MASALALARI = "Matematika, Ona tili, Fizika, Tarix"

# Rolga qarab so'raladigan uchinchi maydon nomi.
ROL_UCHUNCHI_MAYDON = {
    ARIZA_ROL_OQUVCHI: "Sinfingiz",
    ARIZA_ROL_OQITUVCHI: "Kasbingiz (o'qitayotgan fanningiz)",
}
# Tasdiqlangan xabar matni (kalit — rol).
ROL_TASDIQLANDI_XABARI = {
    ARIZA_ROL_OQUVCHI: "🎓 <b>O'quvchi</b> sifatida a'riza yuborasiz.",
    ARIZA_ROL_OQITUVCHI: "👨‍🏫 <b>O'qituvchi</b> sifatida a'riza yuborasiz.",
}

# Bosqich savollari. Bitta joyda saqlanadi: bir xil savol bir necha marta
# yuboriladi (asosiy oqim, uzun matnli qayta kiritish, «❓ Yordam»dan keyin
# savolni qaytarish) — har birida alohida yozilsa, matnlar ajralib qoladi.
SAVOL_FISH = "1️⃣ Ism-familiyangizni yozing:"
SAVOL_TELEFON = "2️⃣ Endi telefon raqamingizni yuboring:"
SAVOL_SINF = f"3️⃣ Endi sinfingizni yozing (masalan: {SINF_MASALALARI}):"
SAVOL_KASB = f"3️⃣ Qaysi fanni dars berasiz? (masalan: {KASB_MASALALARI}):"


def _menyu_tugmasi_bosilganmi(text: str | None) -> bool:
    """Ariza bosqichida pastdagi menyu tugmasi bosildimi?

    Aks holda foydalanuvchi "📚 Kategoriyalar" bosganida u "sinf" yoki
    "kasb" sifatida yuborilib, ariza behuda bo'lib ketardi."""
    return (text or "").strip() in ASOSIY_TUGMALAR


def joriy_savol(state: str | None, ma_lumot: dict | None = None) -> str:
    """Ariza bosqichiga mos savol matnini qaytaradi.

    `❓ Yordam` bosilganda ariza bekor qilinmaydi — foydalanuvchiga yordam
    ko'rsatilib, keyin shu yerda o'sha savol qaytariladi. Shu sababli savol
    matnlari bitta manbadan (`SAVOL_*`) olinadi.
    """
    ma_lumot = ma_lumot or {}
    if state == Ariza.fish.state:
        return SAVOL_FISH
    if state == Ariza.telefon.state:
        return SAVOL_TELEFON
    if state == Ariza.kasb.state:
        return SAVOL_KASB
    if state == Ariza.sinf.state:
        return SAVOL_SINF
    # Bosqich noma'lum bo'lsa ham o'quvchi roli bo'yicha umumiy savol beriladi.
    if ma_lumot.get("rol") == ARIZA_ROL_OQITUVCHI:
        return SAVOL_KASB
    return SAVOL_SINF


async def _menyu_tugmasi_javobi(message: Message, savol: str) -> None:
    """Eski menyu tugmasi matn sifatida yuborilsa — maydonga qaytaradi.

    Eski versiyalarda pastdagi katta tugmalar mavjud edi. Ular enda
    ko'rsatilmaydi (menyu — standart «Menu» tugmasi orqali), lekin eski
    klientlarda yoki eski xabarlarda qolgan bo'lishi mumkin. Bunday matn
    maydonga tushsa, ariza behuda bo'lib ketardi — shuning uchun qaytarib
    beramiz.
    """
    await message.answer(
        f"{savol}\n\n"
        "⚠️ Bu menyu tugmasi eski versiya qoldig'i — u endi ishlatilmaydi.\n"
        "Ariza to'ldirishni davom ettiring, menyuga o'tish uchun esa "
        "pastdagi «Menu» tugmasini yoki /menu buyrug'ini ishlating."
    )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id

    # Eski versiyalarda pastdagi KATTA tugmalar mavjud edi. Telegram'da
    # pastdagi klaviatura butun chat bo'ylab saqlanadi — hozirgi menyu esa
    # standart «Menu» tugmasi orqali ochiladi. Shuning uchun eski
    # klaviaturani bir marta tozalaymiz (yuborilmasa, foydalanuvchi uni
    # ko'rib turaveradi).
    await message.answer(
        "📎 Endi menyu — xabar yozish maydonining pastki chap burchagidagi "
        "standart «Menu» tugmasi orqali ochiladi.",
        reply_markup=klaviatura_olib_tashla(),
    )

    # Bog'langanmi? Oquvchi topilmasa 404 "topilmadi" qaytaradi.
    try:
        await api.kitoblarim(telegram_id)
        await message.answer(
            "Yana xush kelibsiz! 📚 Kerakli bo'limni tanlang:",
            reply_markup=menyu_tugmalari(),
        )
        return
    except ApiXato as e:
        if e.kod != "topilmadi":
            await message.answer(f"Xatolik yuz berdi: {x(e.detail)}")
            return

    # Bog'lanmagan — ariza holatini tekshiramiz.
    try:
        holat = await api.ariza_holati(telegram_id)
    except ApiXato as e:
        await message.answer(f"Xatolik yuz berdi: {x(e.detail)}")
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

    await _rol_tanlash(message)


async def _rol_tanlash(message: Message):
    """Ariza yuboruvchi rolini tanlash uchun inline tugmalarni ko'rsatadi."""
    await message.answer(
        "Kutubxona botidan foydalanish uchun avval a'zo bo'lishingiz kerak.\n\n"
        "A'riza yuborish uchun o'zingizning rolingizni tanlang:",
        reply_markup=ariza_rol_tugmalari(),
    )


def rol_tanlash_xabari(rol):
    """Rol tanlangandan keyin yuboriladigan xabar matni.

    Alohida funksiya qilib ajratilgan, chunki ichidagi nomlar (masalan
    `ROL_UCHUNCHI_MAYDON`) ish vaqtida `NameError` bersa, matnni shu yerda
    tekshirib bo'ladi (bot/_check.py) — serverda esa butun oqim buzilardi.
    """
    return (
        f"{ROL_TASDIQLANDI_XABARI[rol]}\n\n"
        "Ro'yxatga olish uchun 3 ta ma'lumot kerak:\n"
        "1️⃣ Ism-familiyangiz\n"
        "2️⃣ Telefon raqamingiz\n"
        f"3️⃣ {ROL_UCHUNCHI_MAYDON[rol]}"
    )


@router.callback_query(F.data.startswith("ariza_rol:"))
async def ariza_rol_tanlandi(callback: CallbackQuery, state: FSMContext):
    """Rol tugmasi bosilganda rolni saqlaydi va ariza bo'sh bosqichini boshlaydi."""
    rol = (callback.data or "").partition(":")[2]
    if rol not in ROL_TASDIQLANDI_XABARI:
        await callback.answer("Noma'lum ro'l.", show_alert=True)
        return

    # Tugma eski xabarda qolib qolgan bo'lishi mumkin — ariza allaqon
    # ko'rib chiqilayotgan bo'lsa, boshidan o'tkazmaymiz.
    try:
        holat = await api.ariza_holati(callback.from_user.id)
    except ApiXato as e:
        await callback.answer(f"Xatolik yuz berdi: {e.detail}", show_alert=True)
        return
    if holat.get("holati") == "kutmoqda":
        await callback.answer(KUTILMOQDA_XABAR, show_alert=True)
        return

    await state.clear()
    await state.update_data(rol=rol)
    await state.set_state(Ariza.fish)

    await callback.answer()
    if callback.message is None:
        return
    await xabarni_tahrirlash(callback, rol_tanlash_xabari(rol))
    # Rol xabari inline tugmalar bilan berilgan — o'sha xabar
    # tahrirlanadi, maydon uchun yangi xabar yuboriladi. Pastdagi klaviatura
    # endi faqat telefon bosqichida (kontakt yuborish) kerak bo'ladi.
    await callback.message.answer(
        SAVOL_FISH,
    )


@router.message(Ariza.fish)
async def ariza_fish(message: Message, state: FSMContext):
    fish = (message.text or "").strip()
    if not fish:
        await message.answer("Iltimos, ism-familiyangizni matn ko'rinishida yozing.")
        return
    if _menyu_tugmasi_bosilganmi(fish):
        await _menyu_tugmasi_javobi(message, SAVOL_FISH)
        return
    if len(fish) > 130:
        await message.answer("Ism-familiya juda uzun (maksimum 130 belgi). Qayta yozing:")
        return

    await state.update_data(fish=fish)
    await state.set_state(Ariza.telefon)
    await message.answer(
        f"2️⃣ Rahmat. {SAVOL_TELEFON}",
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
            "Quyidagi formatlar to'g'ri keladi: +998901234567, +998 90 123 45 67.\n"
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
    """Raqamni saqlaydi va keyingi bosqichga o'tadi.

    Telefon qabul qilingach, kontakt tugmasi klaviaturasi butunlay
    olib tashlanadi: qolgan maydonlar (sinf/kasb) — oddiy matn, ya'ni
    maydon yonida tugma kerak emas. Menyu esa standart «Menu» tugmasi
    orqali mavjudligini saqlaydi.
    """
    data = await state.get_data()
    rol = data.get("rol", ARIZA_ROL_OQUVCHI)

    await state.update_data(telefon=telefon)
    if rol == ARIZA_ROL_OQITUVCHI:
        await state.set_state(Ariza.kasb)
        await message.answer(
            f"✅ Telefon raqamingiz muvaffaqiyatli tasdiqlandi: {telefon}\n\n"
            f"{SAVOL_KASB}",
            reply_markup=klaviatura_olib_tashla(),
        )
        return

    await state.set_state(Ariza.sinf)
    await message.answer(
        f"✅ Telefon raqamingiz muvaffaqiyatli tasdiqlandi: {telefon}\n\n"
        f"{SAVOL_SINF}",
        reply_markup=klaviatura_olib_tashla(),
    )


@router.message(Ariza.sinf)
async def ariza_sinf(message: Message, state: FSMContext):
    sinf = (message.text or "").strip()
    if not sinf:
        await message.answer(f"Iltimos:\n\n{SAVOL_SINF}")
        return
    if _menyu_tugmasi_bosilganmi(sinf):
        await _menyu_tugmasi_javobi(message, SAVOL_SINF)
        return
    if len(sinf) > 30:
        await message.answer("Sinf nomi juda uzun (maksimum 30 belgi). Qayta yozing:")
        return

    data = await state.get_data()
    await _arizani_yuborish(
        message,
        state,
        data,
        sinf=sinf,
        kasb="",
        savol=SAVOL_SINF,
    )


@router.message(Ariza.kasb)
async def ariza_kasb(message: Message, state: FSMContext):
    """O'qituvchi arizasi uchun o'qitayotgan fanni qabul qiladi."""
    kasb = (message.text or "").strip()
    if not kasb:
        await message.answer(f"Iltimos:\n\n{SAVOL_KASB}")
        return
    if _menyu_tugmasi_bosilganmi(kasb):
        await _menyu_tugmasi_javobi(message, SAVOL_KASB)
        return
    if len(kasb) > 60:
        await message.answer("Kasb nomi juda uzun (maksimum 60 belgi). Qayta yozing:")
        return

    data = await state.get_data()
    await _arizani_yuborish(
        message,
        state,
        data,
        sinf="",
        kasb=kasb,
        savol=SAVOL_KASB,
    )


@router.message(Command("bekor", "start_over", "cancel"))
async def ariza_bekor_qilish(message: Message, state: FSMContext):
    """Ariza to'ldirishdan voz kechish — holat tozalanadi, bot yana ishlaydi."""
    await state.clear()
    await message.answer(
        "Bekor qilindi. Qayta urinish uchun /start yoki /menu buyrug'ini "
        "ishlating.",
        reply_markup=klaviatura_olib_tashla(),
    )


async def _arizani_yuborish(
    message: Message,
    state: FSMContext,
    data: dict,
    sinf: str = "",
    kasb: str = "",
    savol: str = "",
):
    telegram_id = message.from_user.id
    rol = data.get("rol", ARIZA_ROL_OQUVCHI)
    try:
        await api.ariza_yubor(
            telegram_id=telegram_id,
            fish=data["fish"],
            telefon=data["telefon"],
            rol=rol,
            sinf=sinf,
            kasb=kasb,
        )
    except ApiXato as e:
        # Terminal xatolar — holat tozalanadi (yoki ariza allaqon yuborilgan).
        if e.kod in ("allaqachon_azo", "ariza_kutmoqda"):
            await state.clear()
            xabarlar = {
                "allaqachon_azo": "Siz allaqachon ro'yxatdan o'tgansiz. /start bosing.",
                "ariza_kutmoqda": KUTILMOQDA_XABAR,
            }
            await message.answer(xabarlar[e.kod])
            return

        # Validatsiya xatosi: holatni TOZALAMAYMIZ — aks holda foydalanuvchi
        # qayta yozganda bot jim qolib ketardi. Savolni takrorlab, bir xil
        # maydonni qayta kiritishga ruxsat beramiz.
        logger.warning("ariza rad etildi (%s): %s", e.kod, e.detail)
        await message.answer(
            f"⚠️ {x(e.detail)}\n\n{savol}\n"
            "(Bekor qilish uchun /bekor)"
        )
        return

    await state.clear()
    uchinchi_qator = f"🎓 Sinf: {x(sinf)}" if rol == ARIZA_ROL_OQUVCHI else f"📚 Kasb: {x(kasb)}"
    await message.answer(
        "✅ Arizangiz yuborildi!\n\n"
        f"📋 Ism: {x(data['fish'])}\n"
        f"📞 Telefon: {x(data['telefon'])}\n"
        f"{uchinchi_qator}\n\n"
        "Kutubxonachi arizangizni tasdiqlagach, /start buyrug'ini bosing va "
        "botdan foydalanasiz. Tasdiqlash yoki rad etish natijasi shu yerga "
        "xabar qilinadi.",
        reply_markup=klaviatura_olib_tashla(),
    )
