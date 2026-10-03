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

import config
from api_client import api
from handlers import kutubxonachi, noma_lum, qidiruv, shaxsiy, start


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