from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api_client import ApiXato, api
from keyboards import KITOB_QIDIRISH, kitob_batafsil_tugmasi, navbatga_turish_tugmasi
from states import Qidiruv

router = Router(name="qidiruv")

KO_RSATILADIGAN_SONI = 5


@router.message(F.text == KITOB_QIDIRISH)
async def qidiruv_boshla(message: Message, state: FSMContext):
    await state.set_state(Qidiruv.matn)
    await message.answer("Kitob nomi, muallif yoki ISBN ni yozing:")


@router.message(Qidiruv.matn)
async def qidiruv_natija(message: Message, state: FSMContext):
    await state.clear()
    q = (message.text or "").strip()
    if not q:
        await message.answer("Iltimos, qidiruv so'zini kiriting.")
        return

    try:
        natijalar = await api.kitob_qidir(q)
    except ApiXato as e:
        await message.answer(f"Qidiruvda xatolik: {e.detail}")
        return

    if not natijalar:
        await message.answer("Hech narsa topilmadi. Boshqa nom bilan urinib ko'ring.")
        return

    for kitob in natijalar[:KO_RSATILADIGAN_SONI]:
        matn = (
            f"📖 <b>{kitob['nomi']}</b> — {kitob['muallif']} ({kitob['nashr_yili']})\n"
            f"Mavjud: {kitob['mavjud_nusxalar']} / {kitob['jami_nusxalar']}"
        )
        await message.answer(matn, reply_markup=kitob_batafsil_tugmasi(kitob["id"]))

    if len(natijalar) > KO_RSATILADIGAN_SONI:
        await message.answer(
            f"Jami {len(natijalar)} ta natija topildi. Aniqroq so'rov bilan qayta izlang."
        )


@router.callback_query(F.data.startswith("kitob:"))
async def kitob_kartochka(callback: CallbackQuery):
    kitob_id = int(callback.data.split(":")[1])

    try:
        kitob = await api.kitob_detail(kitob_id)
    except ApiXato as e:
        await callback.answer(e.detail, show_alert=True)
        return

    mavjud_nusxa = next((n for n in kitob["nusxalar"] if n["holati"] == "mavjud"), None)

    matn = (
        f"📖 <b>{kitob['nomi']}</b>\n"
        f"Muallif: {kitob['muallif']}\n"
        f"Janr: {kitob['janr']}\n"
        f"Nashriyot: {kitob.get('nashriyot') or '-'} ({kitob['nashr_yili']})"
    )
    if kitob.get("tavsif"):
        matn += f"\n\n{kitob['tavsif']}"

    if mavjud_nusxa:
        javon = mavjud_nusxa.get("javon") or "kutubxonachidan so'rang"
        matn += f"\n\n✅ Kutubxonaga kelib oling, javon: {javon}"
        await callback.message.answer(matn)
    else:
        matn += "\n\n❌ Hozircha mavjud nusxa yo'q."
        await callback.message.answer(matn, reply_markup=navbatga_turish_tugmasi(kitob_id))

    await callback.answer()


@router.callback_query(F.data.startswith("navbat_tur:"))
async def navbatga_tur(callback: CallbackQuery):
    kitob_id = int(callback.data.split(":")[1])
    telegram_id = callback.from_user.id

    try:
        natija = await api.navbatga_tur(kitob_id, telegram_id)
    except ApiXato as e:
        xabarlar = {
            "allaqachon_navbatda": "Siz bu kitobga allaqachon navbatdasiz.",
            "oquvchi_bloklangan": "Sizning kartangiz bloklangan.",
            "oquvchi_topilmadi": "Avval /start orqali kartangizni bog'lang.",
        }
        await callback.answer(xabarlar.get(e.kod, e.detail), show_alert=True)
        return

    await callback.message.answer(
        f"🕐 Siz navbatda {natija['orin']}-o'rindasiz. Nusxa bo'shashi bilan xabar beramiz."
    )
    await callback.answer()