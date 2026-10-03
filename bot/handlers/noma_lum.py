"""Oxirgi "tutqaloq" router: boshqa hech bir handler ishga tushmagan
xabarlarga javob beradi.

Sabab: foydalanuvchi qandaydir xato bosqichda (masalan API xatosi yoki bot
restarti) qolsa, uning xabariga hech qanday handler javob bermaydi va bot
jim qolib ketadi — foydalanuvchi "javob kelmadi" deb hisoblaydi. Shu router
botga hech qachon jim qolmaslikni ta'minlaydi.

Router `main.py` da OXIRGI bo'lib ulanadi — shuning uchun oldingi
handler'lar ishlagan taqdirda bu handler chaqirilmaydi.
"""
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router(name="noma_lum")


@router.message()
async def noma_lum_xabar(message: Message, state: FSMContext):
    holat = await state.get_state()

    if holat:
        await message.answer(
            "🤔 Kutilgan ma'lumotni tushunmadim.\n\n"
            "Ariza to'ldirayotgan bo'lsangiz, savolga matn ko'rinishida javob "
            "bering yoki qayta boshlash uchun /bekor bosing."
        )
        return

    await message.answer(
        "🤖 Men faqat tanlangan bo'limlar bo'yicha ishlayman.\n"
        "Boshlash uchun /start buyrug'ini bosing."
    )