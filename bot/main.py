"""Kutubxona Telegram boti. Ishga tushirish (loyiha ildizidan, Kutubxona/):

    python bot/main.py

Django server (runserver) ishlab turgan bo'lishi kerak — bot faqat
/api/... orqali ishlaydi, bazaga to'g'ridan-to'g'ri ulanmaydi.
"""
import asyncio
import logging
from urllib.parse import urlsplit

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.types import ErrorEvent, MenuButtonCommands
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

import config
from api_client import api
from keyboards import bot_buyruglar
from handlers import (
    kutubxonachi,
    navigatsiya,
    noma_lum,
    qidiruv,
    reviews,
    shaxsiy,
    staff_link,
    start,
)
from subscription import SubscriptionMiddleware


async def xatolik_handler(event: ErrorEvent):
    """Kutilmagan xatolarni foydalanuvchiga ko'rsatadi.

    Aks holda butun oqim jim qoladi: foydalanuvchi tugma bosadi, lekin
    javob kelmaydi (ayniqsa "message is not modified" yoki xizmat akkaunti
    xatolari bo'lganda)."""
    logger = logging.getLogger("bot.xato")
    logger.exception("Kutilmagan xato: %s", event.exception, exc_info=event.exception)

    xabar = (
        "⚠️ Botda nosozlik yuz berdi.\n\n"
        "Iltimos, bir oz vaqtdan keyin qayta urinib ko'ring. Muammo davom etsa "
        "kutubxonachiga xabar bering.\n"
        "Xatoni bekor qilish uchun /bekor bosing."
    )
    try:
        update = event.update
        if update.callback_query:
            await update.callback_query.answer(
                "⚠️ Xatolik yuz berdi.", show_alert=True
            )
            # `message` None bo'lishi mumkin (inline xabar o'chirilgan) —
            # `.answer` chaqirilsa AttributeError chiqar, u ham ushbu
            # try/except ichida ushlanadi, lekin foydalanuvchi hech narsa
            # ko'rmaydi. Shuning uchun oldin tekshiramiz.
            if update.callback_query.message:
                await update.callback_query.message.answer(xabar)
        elif update.message:
            await update.message.answer(xabar)
        else:
            # Inline_query, poll va boshqa update turlari — javob yo'q.
            logger.debug("Javob beriladigan xabar yo'q: %s", type(update).__name__)
    except Exception:
        logger.warning("Xatolik xabari yuborilmadi", exc_info=True)


async def menyu_tugmasini_yoqish(bot: Bot) -> None:
    """Standart Telegram «Menu» tugmasini yoqadi va buyruqlarni ro'yxatlaydi.

    `setChatMenuButton` — tugma xabar yozish maydonining PASTKI CHAP
    burchagida, 📎 yonida paydo bo'ladi (chat ichidagi katta tugmalar
    o'rniga). `MenuButtonCommands` tanlansa, tugma bosilganda Telegram
    buyruqlar ro'yxatini ochadi.

    Sozlamalar Telegram serverida saqlanadi, shuning uchun bot qayta
    ishga tushsa ham yo'qolmaydi. Ammo xavfsizlik uchun har startda
    qayta yuboriladi (idempotent) va natija `getChatMenuButton` bilan
    tekshiriladi — "chaqirildi" deb olish o'rniga haqiqatan o'rnatilganini
    ko'ramiz.
    """
    log = logging.getLogger(__name__)

    await bot.set_my_commands(bot_buyruglar())
    # chat_id bermaslik — barcha shaxsiy chatlar uchun standart sozlamani
    # o'rnadi (guruhlarda alohida chat_id bilan berilishi mumkin).
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    # Ro'yxatni qayta o'qib, Telegram haqiqatan saqlaganini tekshiramiz.
    ornatilgan = await bot.get_chat_menu_button()
    buyruqlar = await bot.get_my_commands()
    if not isinstance(ornatilgan, MenuButtonCommands):
        log.error("«Menu» tugmasi o'rnatilmadi: %r", ornatilgan)
    log.info(
        "«Menu» tugmasi yoqilgan, buyruqlar: %d ta",
        len(buyruqlar),
    )


async def _fsm_storage():
    """FSM holati Redis'da: bot qayta ishga tushsa ham ariza to'ldirayotganlar yo'qolmaydi.

    Redis yo'q bo'lsa xotira storage'iga tushadi (bot baribir ishlaydi).
    """
    try:
        storage = RedisStorage.from_url(
            config.FSM_REDIS_URL,
            key_builder=DefaultKeyBuilder(prefix="kutubxona-bot"),
            state_ttl=86400,
            data_ttl=86400,
        )
        await storage.redis.ping()
        logging.getLogger(__name__).info("FSM: Redis")
        return storage
    except Exception:
        logging.getLogger(__name__).warning("Redis topilmadi — FSM xotirada (qayta ishga tushganda yo'qoladi)")
        return MemoryStorage()


async def _serve_webhook(bot, dp):
    """Receive updates over HTTPS instead of long polling.

    The webhook is left in place on shutdown, so Telegram keeps updates
    queued while the service restarts and nothing is lost.
    """
    if not config.WEBHOOK_SECRET:
        raise RuntimeError("BOT_WEBHOOK_SECRET is required with BOT_WEBHOOK_URL")
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=config.WEBHOOK_SECRET).register(
        app, path=urlsplit(config.WEBHOOK_URL).path
    )
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, config.WEBHOOK_HOST, config.WEBHOOK_PORT).start()
    await bot.set_webhook(
        config.WEBHOOK_URL,
        secret_token=config.WEBHOOK_SECRET,
        allowed_updates=dp.resolve_used_update_types(),
    )
    logging.getLogger(__name__).info(
        "Bot ishga tushdi (webhook, %s:%s)", config.WEBHOOK_HOST, config.WEBHOOK_PORT
    )
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=await _fsm_storage())

    dp.errors.register(xatolik_handler)

    # Buyruqlar va pastdagi menyu tugmalari BIRINCHI — ular FSM state'iga
    # bog'langan handler'lardan oldin turishi shart, aks holda ariza
    # to'ldirilayotganda `/bekor` yoki "📚 Kategoriyalar" kabi tugmalar
    # ariza maydoniga matn sifatida tushib ketadi (batafsil: handlers/
    # navigatsiya.py).
    # Mandatory channel subscription runs before every handler.
    dp.message.outer_middleware(SubscriptionMiddleware())
    dp.callback_query.outer_middleware(SubscriptionMiddleware())
    # Staff linking (/start staff_<code>) must win over the generic /start.
    dp.include_router(staff_link.router)
    dp.include_router(navigatsiya.router)
    dp.include_router(start.router)
    dp.include_router(qidiruv.router)
    dp.include_router(shaxsiy.router)
    dp.include_router(kutubxonachi.router)
    dp.include_router(reviews.router)
    # Oxirida — boshqa hech narsa javob bermasa, foydalanuvchi hech qachon
    # jim qolmasin (masalan ariza bosqichida API xatosi yuz berganda).
    dp.include_router(noma_lum.router)

    try:
        if not config.WEBHOOK_URL:
            await bot.delete_webhook(drop_pending_updates=True)
        try:
            await menyu_tugmasini_yoqish(bot)
        except TelegramAPIError:
            # Sozlama muhim, lekin botni ishga tushirishdan to'smasin —
            # bo'lmasa foydalanuvchi hech qanday javob olmay qoladi.
            logging.getLogger(__name__).exception(
                "«Menu» tugmasi yoqilmadi, bot baribir ishga tushmoqda"
            )
        if config.WEBHOOK_URL:
            await _serve_webhook(bot, dp)
        else:
            logging.getLogger(__name__).info("Bot ishga tushdi (polling)...")
            await dp.start_polling(bot)
    finally:
        await api.yopish()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())