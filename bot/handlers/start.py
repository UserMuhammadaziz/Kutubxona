import logging
import re

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
    asosiy_tugmalar_klaviaturasi,
    fan_tugmalari,
    klaviatura_olib_tashla,
    matndan_telefon_keltirish,
    telefon_keltirish,
    telefon_sorash,
)
from fanlar import FANLAR
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

# Qat'iy format talablari. Birortasi buzilsa ariza boshidan qayta boshlanadi.
SINF_RE = re.compile(r"^(?:[1-9]|1[01])-[A-Za-z]?$")
FISH_RE = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)+$", re.UNICODE)

FORMAT_XATO_XABAR = (
    "❌ Ma'lumot belgilangan formatda yozilmadi.\n\n"
    "Ariza faqat quyidagi tartibda to'ldiriladi:\n"
    "1️⃣ Ism-familiya — «Ali Valiyev» ko'rinishida (kamida ikki so'z);\n"
    "2️⃣ Telefon — «+998901234567» ko'rinishida;\n"
    "3️⃣ Sinf — «7-A» ko'rinishida yoki fan — tugmalardan tanlanadi.\n\n"
    "Arizani boshidan qayta to'ldirishingiz kerak. Rolnizni tanlang:"
)

QAYTA_ARIZA_XABAR = (
    "⚠️ Sizning oldingi arizangiz belgilangan formatda to'ldirilmagan.\n\n"
    "Kutubxonaga qabul qilingan bo'lsangiz ham, yangi qoidalarga muvofiq "
    "arizani boshidan, aynan ko'rsatilgan formatda qaytadan yuborishingiz "
    "kerak. Rolnizni tanlang:"
)

# Rolga qarab so'raladigan uchinchi maydon nomi.
ROL_UCHUNCHI_MAYDON = {
    ARIZA_ROL_OQUVCHI: "Sinfingiz",
    ARIZA_ROL_OQITUVCHI: "Kasbingiz (o'qitayotgan finingiz)",
}
# Tasdiqlangan xabar matni (kalit — rol).
ROL_TASDIQLANDI_XABARI = {
    ARIZA_ROL_OQUVCHI: "🎓 <b>O'quvchi</b> sifatida ariza yuborasiz.",
    ARIZA_ROL_OQITUVCHI: "👨‍🏫 <b>O'qituvchi</b> sifatida ariza yuborasiz.",
}

# Bosqich savollari. Bitta joyda saqlanadi: bir xil savol bir necha marta
# yuboriladi (asosiy oqim, uzun matnli qayta kiritish, «❓ Yordam»dan keyin
# savolni qaytarish) — har birida alohida yozilsa, matnlar ajralib qoladi.
SAVOL_FISH = "1️⃣ Ism-familiyangizni yozing:"
SAVOL_TELEFON = "2️⃣ Endi telefon raqamingizni yuboring:"
SAVOL_SINF = (
    f"3️⃣ Endi sinfingizni yozing (masalan: {SINF_MASALALARI}):\n"
    "⚠️ Faqat «7-A» ko'rinishida yozing. Xato yozilsa ariza boshidan "
    "qayta to'ldiriladi."
)
SAVOL_KASB = (
    "3️⃣ Qaysi fan(lar)ni dars berasiz? Pastdagi ro'yxatdan tanlang.\n"
    "Tanlangan fanlar ✅ bilan belgilanadi. Oxirida «✅ Tayyor» bosing.\n"
    "⚠️ Fanlarni o'zingiz yozmang — xato yozilsa ariza boshidan qayta "
    "to'ldiriladi."
)


def _menyu_tugmasi_bosilganmi(text: str | None) -> bool:
    """Ariza bosqichida pastdigi menyu tugmasi bosildimi?

    Tugmalar endi pastdigi klaviaturada ko'rinadi va ular matn yuboradi.
    Agar himoya qo'yilmasa, "Mening kitoblarim" bosilganda u "sinf" yoki
    "kasb" sifatida qabul qilinib, ariza behuda bo'lib ketardi."""
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
    # Bosqich noma'lum bo'lsa ham oquvchi roli bo'yicha umumiy savol beriladi.
    if ma_lumot.get("rol") == ARIZA_ROL_OQITUVCHI:
        return SAVOL_KASB
    return SAVOL_SINF


async def _format_xato(message: Message, state: FSMContext, sabab: str = "") -> None:
    """Format buzildi — arizani butunlay qaytadan boshlashga majbur qiladi.

    FSM tozalanadi va foydalanuvchiga format qoidalari bilan birga rolli
    tanlash tugmalari yuboriladi. Shu tariqa u 1-bosqichdan qaytadan boshlaydi.
    """
    await state.clear()
    matn = FORMAT_XATO_XABAR
    if sabab:
        matn = f"❌ {sabab}\n\n" + FORMAT_XATO_XABAR
    await _rol_tanlash(message, matn)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id

    # Avval ariza holatini tekshiramiz: eski formatdagi arizalar (qabul
    # qilinganlar ham) yangi formatda qaytadan topshirilishi shart.
    try:
        holat = await api.ariza_holati(telegram_id)
    except ApiXato as e:
        await message.answer(f"Xatolik yuz berdi: {x(e.detail)}")
        return

    if holat.get("qayta_ariza_kerak"):
        await _rol_tanlash(message, QAYTA_ARIZA_XABAR)
        return

    holati = holat.get("holati")
    if holati == "kutmoqda":
        await message.answer(KUTILMOQDA_XABAR)
        return

    if holati == "bekor":
        izoh = holat.get("izoh") or "Sabab ko'rsatilmagan"
        await message.answer(
            "❌ Oldingi arizangiz rad etilgan.\n"
            f"📝 Sabab: {x(izoh)}\n\n"
            "Qayta urinib ko'rishni xohlaysizmi?"
        )

    # Bog'langanmi? Oquvchi topilmasa 404 "topilmadi" qaytaradi.
    try:
        await api.kitoblarim(telegram_id)
    except ApiXato as e:
        if e.kod != "topilmadi":
            await message.answer(f"Xatolik yuz berdi: {x(e.detail)}")
            return
    else:
        await message.answer(
            "Yana xush kelibsiz! Kerakli bo'limni tanlang:",
            reply_markup=asosiy_tugmalar_klaviaturasi(),
        )
        return

    await _rol_tanlash(message)


async def _rol_tanlash(message: Message, matn: str | None = None):
    """Ariza yuboruvchi rolini tanlash uchun inline tugmalarni ko'rsatadi."""
    # Eski sessiyadan qolgan pastdigi tugmalar ariza maydoniga tushib ketmasin.
    await message.answer("…", reply_markup=klaviatura_olib_tashla())
    await message.answer(
        matn
        or (
            "Kutubxona botidan foydalanish uchun avval a'zo bo'lishingiz kerak.\n\n"
            "Ariza yuborish uchun o'zingizning rolingizni tanlang:"
        ),
        reply_markup=ariza_rol_tugmalari(),
    )


def rol_tanlash_xabari(rol):
    """Rol tanlangandan keyin yuboriladigan xabar matni.

    Alohida funksiya qilib ajratilgan, chunki ichidagi nomlar (masalan
    `ROL_UCHUNCHI_MAYDON`) ish vaqtida `NameError` bersa, matnni shu yerda
    tekshirib bo'ladi (bot/_check_tugmalar.py) — serverda esa butun oqim buzilardi.
    """
    uchinchi_format = (
        "tugmalardan tanlanadi"
        if rol == ARIZA_ROL_OQITUVCHI
        else "«7-A» ko'rinishida"
    )
    return (
        f"{ROL_TASDIQLANDI_XABARI[rol]}\n\n"
        "Ro'yxatga olish uchun 3 ta ma'lumot kerak:\n"
        "1️⃣ Ism-familiyangiz — «Ali Valiyev»\n"
        "2️⃣ Telefon raqamingiz — «+998901234567»\n"
        f"3️⃣ {ROL_UCHUNCHI_MAYDON[rol]} — {uchinchi_format}\n\n"
        "⚠️ Har bir ma'lumot aynan shu formatda bo'lishi kerak. Aks holda "
        "ariza boshidan qayta to'ldiriladi."
    )


@router.callback_query(F.data.startswith("ariza_rol:"))
async def ariza_rol_tanlandi(callback: CallbackQuery, state: FSMContext):
    """Rol tugmasi bosilganda rolni saqlaydi va ariza bo'sh bosqichini boshlaydi."""
    rol = (callback.data or "").partition(":")[2]
    if rol not in ROL_TASDIQLANDI_XABARI:
        await callback.answer("Noma'lum rol.", show_alert=True)
        return

    # Tugma eski xabarda qolib qolgan bo'lishi mumkin — ariza allaqachon
    # ko'rib chiqilayotgan bo'lsa, boshidan o'tkazmaymiz.
    try:
        holat = await api.ariza_holati(callback.from_user.id)
    except ApiXato as e:
        await callback.answer(f"Xatolik yuz berdi: {e.detail}", show_alert=True)
        return
    # Eski formatdagi (qayta yuborish belgilangan) ariza to'siq bo'lmaydi.
    if holat.get("holati") == "kutmoqda" and not holat.get("qayta_ariza_kerak"):
        await callback.answer(KUTILMOQDA_XABAR, show_alert=True)
        return

    # Arizani to'ldirish jarayonida takroriy bosish ma'lumotlarni yo'q qilmasin.
    joriy_state = await state.get_state()
    if joriy_state and joriy_state.startswith("Ariza:"):
        await callback.answer("Siz allaqachon arizani to'ldirmoqdasiz.", show_alert=True)
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
        await _format_xato(message, state, "Ism-familiya kiritilmadi.")
        return
    if _menyu_tugmasi_bosilganmi(fish):
        await _format_xato(message, state, "Ism-familiya o'rniga menyu tugmasi yuborildi.")
        return
    if len(fish) > 130 or not FISH_RE.fullmatch(fish):
        await _format_xato(
            message,
            state,
            "Ism-familiya «Ali Valiyev» formatida bo'lishi kerak "
            "(kamida ikki so'z, faqat harflar, maksimum 130 belgi).",
        )
        return

    await state.update_data(fish=fish)
    await state.set_state(Ariza.telefon)
    await message.answer(
        f"Rahmat. {SAVOL_TELEFON}",
        reply_markup=telefon_sorash(),
    )


@router.message(Ariza.telefon, F.contact)
async def ariza_telefon(message: Message, state: FSMContext):
    contact = message.contact

    # Telegram Contact boshqa akkauntga tegishli bo'lishi mumkin (kontakt
    # sifatida tanlangan). O'z raqamini tasdiqlashi uchun user_id mos bo'lishi
    # kerak.
    if contact.user_id and contact.user_id != message.from_user.id:
        await _format_xato(
            message, state, "Bu kontakt sizning akkauntingizga tegishli emas."
        )
        return

    telefon = telefon_keltirish(contact.phone_number)
    if not telefon:
        await _format_xato(
            message, state, "Telefon raqam «+998901234567» formatida bo'lishi kerak."
        )
        return

    await _telefon_qabul(message, state, telefon)


@router.message(Ariza.telefon)
async def ariza_telefon_matn(message: Message, state: FSMContext):
    """Tugmani bosmasdan, raqamni oddiy matn ko'rinishida yuborish."""
    matn = (message.text or "").strip()

    # Telefon bosqichida ham menyu tugmasi bosilishi mumkin (eski xabar yoki
    # navbatdagi klaviatura). U raqam emas — savolga qaytarib beramiz.
    if _menyu_tugmasi_bosilganmi(matn):
        await _format_xato(message, state, "Telefon o'rniga menyu tugmasi yuborildi.")
        return

    telefon = matndan_telefon_keltirish(matn)
    if not telefon:
        await _format_xato(
            message, state, "Telefon raqam «+998901234567» formatida bo'lishi kerak."
        )
        return

    await _telefon_qabul(message, state, telefon)


async def _telefon_qabul(message: Message, state: FSMContext, telefon: str):
    """Raqamni saqlaydi va keyingi bosqichga o'tadi.

    Telefon qabul qilingach, kontakt tugmasi klaviaturasi butunlay
    olib tashlanadi: sinf oddiy matn bilan kiritiladi, o'qituvchilar esa
    fan(lar)ni inline tugmalardan tanlaydi. Menyu standart «Menu» tugmasi
    orqali mavjudligini saqlaydi.
    """
    data = await state.get_data()
    rol = data.get("rol", ARIZA_ROL_OQUVCHI)

    await state.update_data(telefon=telefon)
    if rol == ARIZA_ROL_OQITUVCHI:
        await state.update_data(fanlar=[])
        await state.set_state(Ariza.kasb)
        # Avval telefon bosqichidagi kontakt tugmasini olib tashlaymiz,
        # keyin fanlarni tanlash uchun inline klaviaturani beramiz.
        await message.answer(
            f"✅ Telefon raqamingiz muvaffaqiyatli tasdiqlandi: {telefon}",
            reply_markup=klaviatura_olib_tashla(),
        )
        await message.answer(SAVOL_KASB, reply_markup=fan_tugmalari())
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
        await _format_xato(message, state, "Sinf kiritilmadi.")
        return
    if _menyu_tugmasi_bosilganmi(sinf):
        await _format_xato(message, state, "Sinf o'rniga menyu tugmasi yuborildi.")
        return
    if len(sinf) > 30 or not SINF_RE.fullmatch(sinf):
        await _format_xato(
            message,
            state,
            f"Sinf «7-A», «9-B» yoki «10-» formatida yozilishi kerak "
            f"(masalan: {SINF_MASALALARI}).",
        )
        return

    data = await state.get_data()
    await _arizani_yuborish(message, state, data, sinf=sinf, kasb="")


@router.message(Ariza.kasb)
async def ariza_kasb(message: Message, state: FSMContext):
    """O'qituvchi fanlarni faqat tugmalardan tanlashi kerak.

    Matn yuborilsa (hatto to'g'ri fan nomi bo'lsa ham) format buzilgan hisoblanadi
    va ariza boshidan qayta boshlanadi.
    """
    await _format_xato(
        message, state, "Fanlarni o'zingiz yozmang — pastdagi ro'yxatdan tanlang."
    )


@router.callback_query(Ariza.kasb, F.data.startswith("fan:"))
async def ariza_fan_tanlandi(callback: CallbackQuery, state: FSMContext):
    """Fan tugmasi: tanlash/belgini olish, tozalash yoki arizani yuborish."""
    amal = (callback.data or "").partition(":")[2]
    ma_lumot = await state.get_data()
    tanlanganlar = list(ma_lumot.get("fanlar") or [])

    if amal == "tozalash":
        tanlanganlar = []
    elif amal == "tayyor":
        if not tanlanganlar:
            await callback.answer("Avval kamida bitta fan tanlang.", show_alert=True)
            return
        kasb = ", ".join(tanlanganlar)
        if len(kasb) > 60:
            await callback.answer(
                "Juda ko'p fan tanlandi — kamroq fan tanlang.", show_alert=True
            )
            return
        if callback.message is None:
            await callback.answer()
            return
        await state.update_data(fanlar=tanlanganlar)
        await callback.answer()
        await _arizani_yuborish(
            callback.message, state, await state.get_data(), sinf="", kasb=kasb
        )
        return
    else:
        try:
            index = int(amal)
        except ValueError:
            await callback.answer("Noma'lum fan.", show_alert=True)
            return
        if not 0 <= index < len(FANLAR):
            await callback.answer("Noma'lum fan.", show_alert=True)
            return
        fan = FANLAR[index]
        if fan in tanlanganlar:
            tanlanganlar.remove(fan)
        else:
            tanlanganlar.append(fan)

    await state.update_data(fanlar=tanlanganlar)
    await callback.answer()
    if callback.message is None:
        return
    tanlangan_matn = ", ".join(tanlanganlar) or "—"
    await xabarni_tahrirlash(
        callback,
        f"{SAVOL_KASB}\n\n<b>Tanlanganlar:</b> {x(tanlangan_matn)}",
        reply_markup=fan_tugmalari(tanlanganlar),
    )


@router.message(Command("bekor", "start_over", "cancel"))
async def ariza_bekor_qilish(message: Message, state: FSMContext):
    """Ariza to'ldirishdan voz kechish — holat tozalanadi, bot yana ishlaydi."""
    await state.clear()
    await message.answer(
        "Bekor qilindi. Qayta urinish uchun /start buyrug'ini "
        "ishlating.",
        reply_markup=asosiy_tugmalar_klaviaturasi(),
    )


async def _arizani_yuborish(
    message: Message,
    state: FSMContext,
    data: dict,
    sinf: str = "",
    kasb: str = "",
):
    telegram_id = message.from_user.id
    rol = data.get("rol", ARIZA_ROL_OQUVCHI)
    fish = data.get("fish")
    telefon = data.get("telefon")
    if not fish or not telefon:
        logger.error("Ariza ma'lumotlari to'liq emas: fish=%s, telefon=%s", fish, telefon)
        await state.clear()
        await message.answer(
            "⚠️ Ma'lumotlar to'liq emas. Iltimos, /start bosib qayta urinib ko'ring."
        )
        return
    try:
        await api.ariza_yubor(
            telegram_id=telegram_id,
            fish=fish,
            telefon=telefon,
            rol=rol,
            sinf=sinf,
            kasb=kasb,
        )
    except ApiXato as e:
        # Terminal xatolar — holat tozalanadi (yoki ariza allaqachon yuborilgan).
        if e.kod in ("allaqachon_azo", "ariza_kutmoqda"):
            await state.clear()
            xabarlar = {
                "allaqachon_azo": "Siz allaqachon ro'yxatdan o'tgansiz. /start bosing.",
                "ariza_kutmoqda": KUTILMOQDA_XABAR,
            }
            await message.answer(xabarlar[e.kod])
            return

        # Format buzilgani uchun server rad qilsa, ariza boshidan qayta
        # boshlanadi — foydalanuvchi faqat ko'rsatilgan formatda yuborishi kerak.
        logger.warning("ariza rad etildi (%s): %s", e.kod, e.detail)
        await _format_xato(message, state, f"Server arizani qabul qilmadi: {x(e.detail)}")
        return

    await state.clear()
    uchinchi_qator = f"🎓 Sinf: {x(sinf)}" if rol == ARIZA_ROL_OQUVCHI else f"📚 Kasb: {x(kasb)}"
    await message.answer(
        "✅ Arizangiz yuborildi!\n\n"
        f"📋 Ism: {x(fish)}\n"
        f"📞 Telefon: {x(telefon)}\n"
        f"{uchinchi_qator}\n\n"
        "Kutubxonachi arizangizni tasdiqlagach, /start buyrug'ini bosing va "
        "botdan foydalanasiz. Tasdiqlash yoki rad etish natijasi shu yerga "
        "xabar qilinadi.",
        reply_markup=klaviatura_olib_tashla(),
    )
