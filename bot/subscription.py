"""Mandatory channel subscription for the polling bot.

The backend decides (channel setting, staff exemption, Telegram check); the
bot only asks it. Any backend error lets the user through (fail open).
"""
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from api_client import ApiXato, api
from utils import x

logger = logging.getLogger(__name__)

CHECK_CALLBACK = "sub_check"
STAFF_START = "/start staff_"


def gate_text(gate: dict) -> str:
    return (
        "📢 Botdan foydalanish uchun kutubxonamiz kanaliga obuna bo'ling:\n"
        f"<b>{x(gate.get('title') or '')}</b>\n\n"
        "Obuna bo'lgach, «✅ Obuna bo'ldim» tugmasini bosing."
    )


def gate_keyboard(gate: dict) -> InlineKeyboardMarkup:
    rows = []
    if gate.get("url"):
        rows.append([InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=gate["url"])])
    rows.append([InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data=CHECK_CALLBACK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _gate(telegram_id: int, fresh: bool = False):
    try:
        data = await api.subscription(telegram_id, fresh=fresh)
    except ApiXato as e:
        logger.warning("Subscription check skipped: %s", e.detail)
        return None
    return data if data.get("required") else None


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict], Awaitable[Any]],
        event: Any,
        data: dict,
    ) -> Any:
        if isinstance(event, Message):
            if event.chat.type != "private" or event.from_user is None:
                return await handler(event, data)
            if (event.text or "").startswith((STAFF_START, "/ulash")):
                return await handler(event, data)
            gate = await _gate(event.from_user.id)
            if gate is None:
                return await handler(event, data)
            await event.answer(gate_text(gate), reply_markup=gate_keyboard(gate))
            return None

        if isinstance(event, CallbackQuery):
            if event.data == CHECK_CALLBACK:
                gate = await _gate(event.from_user.id, fresh=True)
                if gate is not None:
                    await event.answer("Siz hali kanalga obuna bo'lmagansiz.", show_alert=True)
                    return None
                await event.answer("Rahmat! Endi botdan foydalanishingiz mumkin.")
                if event.message is not None:
                    await event.message.answer("✅ Obuna tasdiqlandi. Boshlash uchun /start bosing.")
                return None
            gate = await _gate(event.from_user.id)
            if gate is None:
                return await handler(event, data)
            await event.answer()
            await event.bot.send_message(
                event.from_user.id, gate_text(gate), reply_markup=gate_keyboard(gate)
            )
            return None

        return await handler(event, data)
