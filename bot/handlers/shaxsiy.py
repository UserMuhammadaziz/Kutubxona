from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

import branding as b
from api_client import ApiXato, api
from keyboards import (
    BANDLARIM,
    JARIMALARIM,
    MENING_KITOBLARIM,
    NAVBATLARIM,
    band_bekor_tugmasi,
    navbatdan_chiqish_tugmasi,
    taklif_javob_tugmalari,
)
from utils import x, xabarni_tahrirlash

router = Router(name="shaxsiy")

BOGLANMAGAN_XABAR = "Avval /start orqali ro'yxatdan o'ting."


def _xatolar(e: ApiXato) -> str:
    """`topilmadi` — kartaga bog'lanmagan; boshqasi — server matni."""
    return BOGLANMAGAN_XABAR if e.kod == "topilmadi" else x(e.detail)


def _berish_qatori(b: dict) -> str:
    """`/loans/my/` bitta yozuvi uchun xabar qatori."""
    # Nusxasi yo'q kitob "asli" holda berilgan bo'ladi — inventar raqami
    # bo'sh shuning uchun "INV: " emas, "Asli kitob" ko'rsatiladi.
    if b.get("asli") or not b.get("inventar_raqami"):
        manzil = "📕 Asli kitob (nusxasi yo'q)"
    else:
        manzil = f"🔖 {x(b['inventar_raqami'])}"

    qator = (
        f"📖 {x(b['kitob_nomi'])} ({manzil})\n"
        f"   Qaytarish muddati: {b['qaytarish_muddati']}"
    )
    qolgan = b["qolgan_kun"]
    if qolgan < 0:
        qator += f"\n   ⚠️ Muddat {abs(qolgan)} kun o'tdi — jarima hisoblanmoqda"
    else:
        qator += f"\n   ⏳ Qolgan kun: {qolgan}"
    return qator


@router.message(F.text == MENING_KITOBLARIM)
async def kitoblarim(message: Message):
    telegram_id = message.from_user.id
    try:
        royxat = await api.kitoblarim(telegram_id)
    except ApiXato as e:
        await message.answer(_xatolar(e))
        return

    if not royxat:
        await message.answer("Sizda hozir kutubxona kitobi yo'q.")
        return

    qatorlar = [_berish_qatori(b) for b in royxat]
    await message.answer("\n\n".join(qatorlar))


@router.message(F.text == JARIMALARIM)
async def jarimalarim(message: Message):
    telegram_id = message.from_user.id
    try:
        natija = await api.jarimalarim(telegram_id)
    except ApiXato as e:
        await message.answer(_xatolar(e))
        return

    jarimalar = natija["jarimalar"]
    if not jarimalar:
        await message.answer("Sizda to'lanmagan jarima yo'q. 🎉")
        return

    qatorlar = [
        f"📖 {x(j['kitob_nomi'])}: {j['kechikkan_kunlar']} kun kechikish — {x(j['summa'])} so'm"
        for j in jarimalar
    ]
    matn = "\n".join(qatorlar)
    matn += f"\n\n💰 Umumiy qarz: {natija['umumiy_qarz']} so'm"
    matn += "\n\nTo'lovni kutubxonachiga topshiring."
    await message.answer(matn)


@router.message(F.text == BANDLARIM)
async def bandlarim(message: Message):
    """Men band qilgan kitoblar va ularning holati."""
    telegram_id = message.from_user.id
    try:
        royxat = await api.bandlarim(telegram_id)
    except ApiXato as e:
        await message.answer(_xatolar(e))
        return

    if not royxat:
        await message.answer(
            f"{b.logo(sarlavha='BANDLARIM')}\n\n"
            "Hozir band qilgan kitobingiz yo'q.\n\n"
            "Kerakli kitobni toping va kartochkasidagi «Band qilish» "
            "tugmasini bosing — so'rov kutubxonachiga yuboriladi va "
            "tasdiqlanganligi xabar qilinadi."
        )
        return

    # Avval kutilayotgan so'rovlar tepada — ularga tugma kerak.
    tartib = {"kutmoqda": 0, "tasdiqlandi": 1, "rad_etildi": 2, "bekor_qilindi": 3}
    royxat = sorted(royxat, key=lambda r: (tartib.get(r["holati"], 9), r.get("so_rov_sanasi") or ""))
    kutilmoqda = sum(1 for r in royxat if r["holati"] == "kutmoqda")

    sarlavha_qismi = (
        f"{b.logo(sarlavha='BANDLARIM')}\n\n"
        f"Jami: <b>{len(royxat)}</b> ta band so'rovi"
        + (f" — <b>{kutilmoqda}</b> tasi kutilmoqda" if kutilmoqda else "")
        + "\n"
        + b.chiziq()
    )
    await message.answer(sarlavha_qismi)

    for r in royxat[:20]:
        qator = (
            f"<b>{x(r['kitob_nomi'])}</b>\n"
            f"{b.band_holati(r['holati'])}"
        )
        if r.get("izoh"):
            qator += f"\n<i>{x(r['izoh'])}</i>"
        if r.get("tasdiqlash_izohi"):
            qator += f"\n<i>Xodim: {x(r['tasdiqlash_izohi'])}</i>"

        if r["holati"] == "kutmoqda":
            await message.answer(
                qator, reply_markup=band_bekor_tugmasi(r["id"])
            )
        else:
            await message.answer(qator)


@router.message(F.text == NAVBATLARIM)
async def navbatlarim(message: Message):
    telegram_id = message.from_user.id
    try:
        royxat = await api.navbatlarim(telegram_id)
    except ApiXato as e:
        await message.answer(_xatolar(e))
        return

    if not royxat:
        await message.answer("Siz hech qanday navbatda emassiz.")
        return

    chiqarilgan = []
    for n in royxat:
        if n["holati"] == "kutmoqda":
            orin = n.get("orin")
            o_rin = f"{orin}-o'rindasiz" if orin else "navbatdasiz"
            chiqarilgan.append(
                (
                    f"📖 {x(n['kitob_nomi'])} — navbatda {o_rin}",
                    navbatdan_chiqish_tugmasi(n["id"]),
                )
            )
        elif n["holati"] == "taklif_qilindi":
            chiqarilgan.append(
                (
                    f"📖 {x(n['kitob_nomi'])} — sizga taklif yuborilgan, javob bering:",
                    taklif_javob_tugmalari(n["id"]),
                )
            )

    if not chiqarilgan:
        await message.answer("Sizning faol navbatingiz yo'q.")
        return

    for matn, tugmalar in chiqarilgan:
        await message.answer(matn, reply_markup=tugmalar)


@router.callback_query(F.data.startswith("navbat_chiq:"))
async def navbatdan_chiq(callback: CallbackQuery):
    qismlar = callback.data.split(":")
    if len(qismlar) < 2 or not qismlar[1].isdigit():
        await callback.answer("Navbat topilmadi.", show_alert=True)
        return
    navbat_id = int(qismlar[1])
    try:
        await api.navbatdan_chiq(navbat_id)
    except ApiXato as e:
        await callback.answer(e.detail, show_alert=True)
        return

    await xabarni_tahrirlash(callback, "🚪 Navbatdan chiqdingiz.")
    await callback.answer()


@router.callback_query(F.data.startswith("navbat_javob:"))
async def navbat_javob_handler(callback: CallbackQuery):
    qismlar = callback.data.split(":")
    if len(qismlar) < 3 or not qismlar[1].isdigit():
        await callback.answer("Bekor qiling.", show_alert=True)
        return
    navbat_id, javob = qismlar[1], qismlar[2]

    try:
        await api.navbat_javob(int(navbat_id), javob)
    except ApiXato as e:
        if e.kod == "muddat_tugagan":
            await xabarni_tahrirlash(callback, "⌛ Afsus, javob muddati tugagan.")
            await callback.answer()
        else:
            await callback.answer(e.detail, show_alert=True)
        return

    if javob == "olaman":
        await xabarni_tahrirlash(
            callback,
            "✅ Nusxa 24 soat siz uchun ushlab turiladi, kutubxonaga kelib oling.",
        )
    else:
        await xabarni_tahrirlash(callback, "❌ Rad etildingiz. Navbat bekor qilindi.")
    await callback.answer()