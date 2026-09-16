from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from api_client import ApiXato, api
from keyboards import (
    JARIMALARIM,
    MENING_KITOBLARIM,
    NAVBATLARIM,
    navbatdan_chiqish_tugmasi,
    taklif_javob_tugmalari,
)

router = Router(name="shaxsiy")

BOGLANMAGAN_XABAR = "Avval /start orqali kartangizni bog'lang."


@router.message(F.text == MENING_KITOBLARIM)
async def kitoblarim(message: Message):
    telegram_id = message.from_user.id
    try:
        royxat = await api.kitoblarim(telegram_id)
    except ApiXato as e:
        await message.answer(BOGLANMAGAN_XABAR if e.kod == "topilmadi" else e.detail)
        return

    if not royxat:
        await message.answer("Sizda hozir kutubxona kitobi yo'q.")
        return

    qatorlar = []
    for b in royxat:
        qator = (
            f"📖 {b['kitob_nomi']} (INV: {b['inventar_raqami']})\n"
            f"   Qaytarish muddati: {b['qaytarish_muddati']}"
        )
        qolgan = b["qolgan_kun"]
        if qolgan < 0:
            qator += f"\n   ⚠️ Muddat {abs(qolgan)} kun o'tdi — jarima hisoblanmoqda"
        else:
            qator += f"\n   Qolgan kun: {qolgan}"
        qatorlar.append(qator)

    await message.answer("\n\n".join(qatorlar))


@router.message(F.text == JARIMALARIM)
async def jarimalarim(message: Message):
    telegram_id = message.from_user.id
    try:
        natija = await api.jarimalarim(telegram_id)
    except ApiXato as e:
        await message.answer(BOGLANMAGAN_XABAR if e.kod == "topilmadi" else e.detail)
        return

    jarimalar = natija["jarimalar"]
    if not jarimalar:
        await message.answer("Sizda to'lanmagan jarima yo'q. 🎉")
        return

    qatorlar = [
        f"📖 {j['kitob_nomi']}: {j['kechikkan_kunlar']} kun kechikish — {j['summa']} so'm"
        for j in jarimalar
    ]
    matn = "\n".join(qatorlar)
    matn += f"\n\nUmumiy qarz: {natija['umumiy_qarz']} so'm"
    matn += "\n\nTo'lovni kutubxonachiga topshiring."
    await message.answer(matn)


@router.message(F.text == NAVBATLARIM)
async def navbatlarim(message: Message):
    telegram_id = message.from_user.id
    try:
        royxat = await api.navbatlarim(telegram_id)
    except ApiXato as e:
        await message.answer(BOGLANMAGAN_XABAR if e.kod == "topilmadi" else e.detail)
        return

    if not royxat:
        await message.answer("Siz hech qanday navbatda emassiz.")
        return

    for n in royxat:
        if n["holati"] == "kutmoqda":
            matn = f"📖 {n['kitob_nomi']} — navbatda {n['orin']}-o'rindasiz"
            await message.answer(matn, reply_markup=navbatdan_chiqish_tugmasi(n["id"]))
        elif n["holati"] == "taklif_qilindi":
            matn = f"📖 {n['kitob_nomi']} — sizga taklif yuborilgan, javob bering:"
            await message.answer(matn, reply_markup=taklif_javob_tugmalari(n["id"]))


@router.callback_query(F.data.startswith("navbat_chiq:"))
async def navbatdan_chiq(callback: CallbackQuery):
    navbat_id = int(callback.data.split(":")[1])
    try:
        await api.navbatdan_chiq(navbat_id)
    except ApiXato as e:
        await callback.answer(e.detail, show_alert=True)
        return

    await callback.message.edit_text("🚪 Navbatdan chiqdingiz.")
    await callback.answer()


@router.callback_query(F.data.startswith("navbat_javob:"))
async def navbat_javob_handler(callback: CallbackQuery):
    _, navbat_id, javob = callback.data.split(":")

    try:
        await api.navbat_javob(int(navbat_id), javob)
    except ApiXato as e:
        if e.kod == "muddat_tugagan":
            await callback.message.edit_text("⌛ Afsus, javob muddati tugagan.")
            await callback.answer()
        else:
            await callback.answer(e.detail, show_alert=True)
        return

    if javob == "olaman":
        await callback.message.edit_text(
            "✅ Nusxa 24 soat siz uchun ushlab turiladi, kutubxonaga kelib oling."
        )
    else:
        await callback.message.edit_text("❌ Rad etildingiz. Navbat bekor qilindi.")
    await callback.answer()