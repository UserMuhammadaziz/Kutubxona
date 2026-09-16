"""Ixtiyoriy (qo'shimcha ball) qism: kutubxonachi botga inventar raqamini
yuborib, kitobni qaytarib olishi mumkin. /qaytar buyrug'i bilan boshlanadi.
"""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api_client import ApiXato, api
from keyboards import qaytarish_tasdiq_tugmasi
from states import KutubxonachiQaytarish

router = Router(name="kutubxonachi")


@router.message(Command("qaytar"))
async def qaytarish_boshla(message: Message, state: FSMContext):
    await state.set_state(KutubxonachiQaytarish.inventar)
    await message.answer("Inventar raqamini yuboring (masalan: INV-000412):")


@router.message(KutubxonachiQaytarish.inventar)
async def inventar_qabul(message: Message, state: FSMContext):
    await state.clear()
    inv = (message.text or "").strip().upper()

    try:
        nusxalar = await api.nusxa_qidir(inv)
    except ApiXato as e:
        await message.answer(f"Xatolik: {e.detail}")
        return

    nusxa = next((n for n in nusxalar if n["inventar_raqami"] == inv), None)
    if not nusxa:
        await message.answer("Bu inventar raqami bilan nusxa topilmadi.")
        return

    try:
        detail = await api.nusxa_detail(nusxa["id"])
    except ApiXato as e:
        await message.answer(f"Xatolik: {e.detail}")
        return

    faol = next(
        (b for b in detail["berish_tarixi"] if not b.get("qaytarilgan_sana")), None
    )
    if not faol:
        await message.answer(f"«{nusxa['kitob_nomi']}» ({inv}) hozir hech kimda emas.")
        return

    matn = (
        f"«{nusxa['kitob_nomi']}» ({inv}) — {faol['oquvchi_fish']} da.\n"
        f"Qaytarib olinsinmi?"
    )
    await message.answer(matn, reply_markup=qaytarish_tasdiq_tugmasi(faol["id"]))


@router.callback_query(F.data.startswith("qaytar:"))
async def qaytarish_tasdiq(callback: CallbackQuery):
    berish_id = int(callback.data.split(":")[1])

    try:
        natija = await api.kitobni_qaytar(berish_id)
    except ApiXato as e:
        await callback.answer(e.detail, show_alert=True)
        return

    matn = "✅ Kitob qaytarib olindi."
    if natija.get("jarima_summasi"):
        matn += f"\n⚠️ Jarima yozildi: {natija['jarima_summasi']} so'm"
    if natija.get("navbatga_taklif_ketdimi"):
        matn += "\n📨 Nusxa navbatdagi keyingi o'quvchiga taklif qilindi."

    await callback.message.edit_text(matn)
    await callback.answer()
    