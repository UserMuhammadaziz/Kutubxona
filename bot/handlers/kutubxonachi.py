"""Ixtiyoriy (qo'shimcha ball) qism: kutubxonachi botga inventar raqamini
yuborib, kitobni qaytarib olishi va band qilingan so'rovlarni tasdiqlashi
mumkin. `/qaytar` buyrug'i bilan qaytarish, `/bandlar` bilan esa band
so'rovlari ro'yxati ochiladi.

Muhim: bu buyruqlar kitobni qaytarib olish yoki tasdiqlashni amalga oshiradi,
ya'ni kutubxonachi huquqiga ega. Bot esa o'z xizmat akkaunti orqali
`IsLibrarian` endpoint'iga uradi — shuning uchun faqat `BOT_ADMIN_CHAT_IDS`
ro'yxatidagi chat_id lar uchun ishlaydi (bo'lmasa buyruq butunlay
o'chiriladi). Band so'rovlarini tasdiqlash veb-panel orqali ham mumkin.
"""
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
import branding as b
from api_client import ApiXato, api
from keyboards import (
    ASOSIY_TUGMALAR,
    band_tasdiq_tugmalari,
    qaytarish_tasdiq_tugmasi,
)
from states import KutubxonachiQaytarish
from utils import x, xabarni_tahrirlash

router = Router(name="kutubxonachi")

# Inventar raqami so'raladigan xabar. `navigatsiya.py` «❓ Yordam»dan keyin
# shu savolni qaytaradi, shuning uchun bitta joyda saqlanadi.
INVENTAR_SAVOLI = "Inventar raqamini yuboring (masalan: INV-000412):"


def sana_vaqt(qiymat: str) -> str:
    """ISO sanani "04.10.2026, 07:02" ko'rinishida qaytaradi.

    Xom qiymat (`2026-10-04T07:02:10Z`) foydalanuvchiga noto'g'ri
    ko'rinardi. `datetime` vaqt zonasi UTC da bo'lgani uchun mahalliy
    ko'rinishga o'tkaziladi.
    """
    try:
        d = datetime.fromisoformat(str(qiymat).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return str(qiymat)
    return d.strftime("%d.%m.%Y, %H:%M")


RUXSAT_YUQ = (
    "Bu buyruq faqat kutubxonachilar uchun.\n\n"
    "Agar siz xodim bo'lsangiz, .env faylidagi BOT_ADMIN_CHAT_IDS ga o'z "
    "Telegram ID ni qo'shib, botni qayta ishga tushiring."
)


async def _ruxsat_berilganmi(message: Message) -> bool:
    """Ruxsat yo'q bo'lsa foydalanuvchiga xabar yuboradi (va False qaytaradi).

    Oldin `message.answer(...)` `await`siz chaqirilardi — shuning uchun
    xabar umuman yuborilmasdi, foydalanuvchi hech narsa ko'rmay qolardi."""
    if config.bot_adminmi(message.from_user.id):
        return True
    await message.answer(RUXSAT_YUQ)
    return False


@router.message(Command("qaytar"))
async def qaytarish_boshla(message: Message, state: FSMContext):
    if not await _ruxsat_berilganmi(message):
        return
    await state.set_state(KutubxonachiQaytarish.inventar)
    # Inventar raqami oddiy matn — pastdagi klaviatura kerak emas.
    await message.answer(INVENTAR_SAVOLI)


@router.message(KutubxonachiQaytarish.inventar)
async def inventar_qabul(message: Message, state: FSMContext):
    if not await _ruxsat_berilganmi(message):
        await state.clear()
        return

    matn = (message.text or "").strip()
    if matn in ASOSIY_TUGMALAR:
        # Pastdagi menyu tugmasi bosilgan — inventar raqami emas.
        await message.answer(INVENTAR_SAVOLI)
        return

    await state.clear()
    inv = matn.upper()

    try:
        nusxalar = await api.nusxa_qidir(inv)
    except ApiXato as e:
        await message.answer(f"Xatolik: {x(e.detail)}")
        return

    nusxa = next((n for n in nusxalar if n["inventar_raqami"] == inv), None)
    if not nusxa:
        await message.answer("Bu inventar raqami bilan nusxa topilmadi.")
        return

    try:
        detail = await api.nusxa_detail(nusxa["id"])
    except ApiXato as e:
        await message.answer(f"Xatolik: {x(e.detail)}")
        return

    faol = next(
        (b for b in detail["berish_tarixi"] if not b.get("qaytarilgan_sana")), None
    )
    if not faol:
        await message.answer(f"«{x(nusxa['kitob_nomi'])}» ({inv}) hozir hech kimda emas.")
        return

    matn = (
        f"«{x(nusxa['kitob_nomi'])}» ({inv})\n"
        f"Kimda: {x(faol['oquvchi_fish'])}\n"
        f"Qaytarib olinsinmi?"
    )
    await message.answer(matn, reply_markup=qaytarish_tasdiq_tugmasi(faol["id"]))


@router.callback_query(F.data.startswith("qaytar:"))
async def qaytarish_tasdiq(callback: CallbackQuery):
    if not config.bot_adminmi(callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return

    qismlar = callback.data.split(":")
    if len(qismlar) < 2 or not qismlar[1].isdigit():
        await callback.answer("Berish topilmadi.", show_alert=True)
        return
    berish_id = int(qismlar[1])

    try:
        natija = await api.kitobni_qaytar(berish_id)
    except ApiXato as e:
        await callback.answer(e.detail, show_alert=True)
        return

    matn = "<b>Kitob qaytarib olindi.</b>"
    if natija.get("jarima_summasi"):
        matn += f"\nJarima yozildi: {natija['jarima_summasi']} so'm"
    if natija.get("navbatga_taklif_ketdimi"):
        matn += "\nNusxa navbatdagi keyingi o'quvchiga taklif qilindi."

    # Agar kitob muddatdan oldin qaytarilgan bo'lsa, xabar o'quvchiga
    # allaqachon yuborilgan (apps/berish/services.py ichida, tranzaksiya
    # commit bo'lganda) — shuning uchun bu yerdan qaytaramiz, aks holda
    # o'quvchiga bir xil xabar ikki marta borar.
    if natija.get("erken_qaytarildi"):
        matn += (
            "\nMuddatdan oldin qaytarildi — o'quvchiga xabar yuborildi, "
            "jarima yozilmadi."
        )

    await xabarni_tahrirlash(callback, matn)
    await callback.answer()


# ------------------------------------------------------- band qilish (tasdiqlash)
async def bandlar_koritaz(message: Message, state: FSMContext):
    """Tasdiqlash kutilayotgan band so'rovlarini ro'yxatlaydi.

    Kutubxonachi/administrator shu yerda bandni tasdiqlaydi (kitob so'rov
    qilgan o'quvchiga beriladi) yoki rad etadi.
    """
    if not await _ruxsat_berilganmi(message):
        return

    try:
        bandlar = await api.bandlar("kutmoqda")
    except ApiXato as e:
        await message.answer(f"Xatolik: {x(e.detail)}")
        return

    if not bandlar:
        await message.answer(
            f"{b.logo(sarlavha='BAND SO\'ROVLARI')}\n\n"
            "Tasdiqlash kutilayotgan so'rov yo'q."
        )
        return

    await message.answer(
        f"{b.logo(sarlavha='BAND SO\'ROVLARI')}\n\n"
        f"Kutilmoqda: <b>{len(bandlar)}</b> ta so'rov\n"
        + b.chiziq()
        + "\n\nHar birini tasdiqlang — kitob so'rov qilgan o'quvchiga beriladi "
        "va unga xabar yuboriladi, yoki rad eting."
    )
    for r in bandlar[:20]:
        rol = "o'qituvchi" if r.get("oquvchi_rol") == "oqituvchi" else "o'quvchi"
        qator = (
            f"<b>{x(r['kitob_nomi'])}</b>\n"
            f"Sohraydi: {x(r['oquvchi_fish'])} · {rol}"
        )
        if r.get("oquvchi_sinf"):
            qator += f" · {x(r['oquvchi_sinf'])}"
        if r.get("so_rov_sanasi"):
            qator += f"\nSo'rov: {sana_vaqt(r['so_rov_sanasi'])}"
        if r.get("izoh"):
            qator += f"\n<i>{x(r['izoh'])}</i>"
        await message.answer(qator, reply_markup=band_tasdiq_tugmalari(r["id"]))


@router.callback_query(F.data.startswith("band_tasdiq:"))
async def bandni_tasdiqlash(callback: CallbackQuery):
    if not config.bot_adminmi(callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return

    qismlar = callback.data.split(":")
    if len(qismlar) < 2 or not qismlar[1].isdigit():
        await callback.answer("So'rov topilmadi.", show_alert=True)
        return

    try:
        natija = await api.bandni_tasdiqla(int(qismlar[1]))
    except ApiXato as e:
        await callback.answer(x(e.detail), show_alert=True)
        return

    await xabarni_tahrirlash(
        callback,
        "<b>Tasdiqlandi</b> — kitob so'rov qilgan o'quvchiga berildi.\n\n"
        f"Kitob: {x(natija.get('kitob_nomi')) or '—'}\n"
        f"O'quvchi: {x(natija.get('oquvchi_fish')) or '—'}\n\n"
        "O'quvchiga qaytarish muddati bilan xabar yuborildi.",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("band_rad:"))
async def bandni_rad_etish(callback: CallbackQuery):
    if not config.bot_adminmi(callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return

    qismlar = callback.data.split(":")
    if len(qismlar) < 2 or not qismlar[1].isdigit():
        await callback.answer("So'rov topilmadi.", show_alert=True)
        return

    try:
        natija = await api.bandni_rad_et(int(qismlar[1]))
    except ApiXato as e:
        await callback.answer(x(e.detail), show_alert=True)
        return

    await xabarni_tahrirlash(
        callback,
        "<b>So'rov rad etildi.</b> Kitob yana boshqalarga berilishi mumkin.\n\n"
        f"Kitob: {x(natija.get('kitob_nomi')) or '—'}\n"
        "O'quvchiga rad etilganligi ham, sababi ham yuborildi.",
    )
    await callback.answer()
    
