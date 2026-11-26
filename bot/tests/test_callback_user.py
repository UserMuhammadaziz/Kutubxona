"""Button presses must act for the user who pressed, never for the bot.

`callback.message` is the bot's own message, so its `from_user` is the bot.
Run from `bot/`: python -m unittest tests.test_callback_user
"""
import datetime
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram import Bot
from aiogram.types import CallbackQuery, Chat, Message, User

from handlers import navigatsiya, start

BOT_USER = User(id=999, is_bot=True, first_name="bot")
READER = User(id=42, is_bot=False, first_name="reader")


def make_callback(data):
    bot = Bot("123:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789")
    message = Message(
        message_id=1,
        date=datetime.datetime.now(),
        chat=Chat(id=42, type="private"),
        from_user=BOT_USER,
        text="menu",
    ).as_(bot)
    return CallbackQuery(id="1", from_user=READER, chat_instance="c", message=message, data=data).as_(bot)


class CallbackUserTest(unittest.IsolatedAsyncioTestCase):
    async def test_teacher_application_uses_presser_id(self):
        state = MagicMock()
        state.get_data = AsyncMock(return_value={"fanlar": ["Matematika"], "fish": "Ali Valiyev", "telefon": "+998901234567", "rol": "oqituvchi"})
        state.update_data = AsyncMock()
        state.clear = AsyncMock()
        with patch.object(start.api, "ariza_yubor", AsyncMock()) as send, patch.object(
            CallbackQuery, "answer", AsyncMock()
        ), patch.object(Message, "answer", AsyncMock()):
            await start.ariza_fan_tanlandi(make_callback("fan:tayyor"), state)
        send.assert_awaited_once()
        self.assertEqual(send.await_args.kwargs["telegram_id"], READER.id)
        self.assertEqual(send.await_args.kwargs["kasb"], "Matematika")

    async def test_menu_button_shows_presser_books(self):
        state = MagicMock()
        state.clear = AsyncMock()
        seen = {}

        async def fake_books(message):
            seen["id"] = message.from_user.id

        with patch.object(navigatsiya.shaxsiy, "kitoblarim", fake_books), patch.object(
            navigatsiya, "_arizani_tugatish", AsyncMock()
        ), patch.object(CallbackQuery, "answer", AsyncMock()):
            await navigatsiya.menyu_bolimi(make_callback("menyu:kitoblarim"), state)
        self.assertEqual(seen["id"], READER.id)


if __name__ == "__main__":
    unittest.main()
