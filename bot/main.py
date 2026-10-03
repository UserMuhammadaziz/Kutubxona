"""Kutubxona Telegram boti. Ishga tushirish (loyiha ildizidan, Kutubxona/):

    python bot/main.py

Django server (runserver) ishlab turgan bo'lishi kerak — bot faqat
/api/... orqali ishlaydi, bazaga to'g'ridan-to'g'ri ulanmaydi.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

import config
from api_client import api
from handlers import (
    kutubxonachi,
    navigatsiya,
    noma_lum,
    qidiruv,
    shaxsiy,
    start,
)


async def xatolik_handler(event: ErrorEvent):
    """Kutilmagan xatolarni foydalanuvchiga ko'rsatadi.

    Aks holda butun oqim jim qoladi: foydalanuvchi tugma bosadi, lekin
    javob kelmaydi (ayniqsa "message is not modified" yoki xizmat akkaunti
    xatolari bo'lganda)."""
    logger = logging.getLogger("bot.xato")
    logger.exception("Kutilmagan xato: %s", event.exception, exc_info=event.exception)

    xabar = (
        "⚠️ Botda nosozlik yuz berdi.\n\n"
        "Iltimos, bir ozdan keyin qayta urinib ko'ring. Muammo davom etsa "
        "kutubxonachiga xabar bering.\n"
        "Xatoni bekor qilish uchun /bekor bosing."
    )
    try:
        if event.update.callback_query:
            await event.update.callback_query.answer("⚠️ Xatolik yuz berdi.", show_alert=True)
            await event.update.callback_query.message.answer(xabar)
        else:
            await event.update.message.answer(xabar)
    except Exception:
        logger.warning("Xatolik xabari yuborilmadi", exc_info=True)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.errors.register(xatolik_handler)

    # Buyruqlar va pastdagi menyu tugmalari BIRINCHI — ular FSM state'iga
    # bog'langan handler'lardan oldin turishi shart, aks holda ariza
    # to'ldirilayotganda `/bekor` yoki "📚 Kategoriyalar" kabi tugmalar
    # ariza maydoniga matn sifatida tushib ketadi (batafsil: handlers/
    # navigatsiya.py).
    dp.include_router(navigatsiya.router)
    dp.include_router(start.router)
    dp.include_router(qidiruv.router)
    dp.include_router(shaxsiy.router)
    dp.include_router(kutubxonachi.router)
    # Oxirida — boshqa hech narsa javob bermasa, foydalanuvchi hech qachon
    # jim qolmasin (masalan ariza bosqichida API xatosi yuz berganda).
    dp.include_router(noma_lum.router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logging.getLogger(__name__).info("Bot ishga tushdi (polling)...")
        await dp.start_polling(bot)
    finally:
        await api.yopish()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())