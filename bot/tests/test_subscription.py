"""Mandatory channel subscription middleware and staff deep-link linking.

Run from `bot/`: python -m unittest tests.test_subscription
"""
import datetime
import unittest
from unittest.mock import AsyncMock, patch

from aiogram import Bot
from aiogram.types import CallbackQuery, Chat, Message, User

import subscription
from api_client import ApiXato
from handlers import staff_link

READER = User(id=42, is_bot=False, first_name="reader")
BOT = Bot("123:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789")
GATE = {"required": True, "title": "Kanal <1>", "url": "https://t.me/kanal"}


def make_message(text, chat_type="private"):
    return Message(
        message_id=1, date=datetime.datetime.now(), chat=Chat(id=42, type=chat_type), from_user=READER, text=text
    ).as_(BOT)


def make_callback(data):
    return CallbackQuery(id="1", from_user=READER, chat_instance="c", message=make_message("menu"), data=data).as_(BOT)


class SubscriptionMiddlewareTest(unittest.IsolatedAsyncioTestCase):
    async def run_mw(self, event, gate):
        handler = AsyncMock(return_value="handled")
        api_call = AsyncMock(side_effect=gate) if isinstance(gate, Exception) else AsyncMock(return_value=gate)
        with patch.object(subscription.api, "subscription", api_call), patch.object(
            Message, "answer", AsyncMock()
        ) as msg_answer, patch.object(CallbackQuery, "answer", AsyncMock()) as cb_answer, patch.object(
            Bot, "send_message", AsyncMock()
        ) as send:
            result = await subscription.SubscriptionMiddleware()(handler, event, {})
        return result, handler, api_call, msg_answer, cb_answer, send

    async def test_unsubscribed_message_is_blocked(self):
        result, handler, _, msg_answer, _, _ = await self.run_mw(make_message("/start"), GATE)
        handler.assert_not_called()
        self.assertIsNone(result)
        text = msg_answer.call_args.args[0]
        self.assertIn("Kanal &lt;1&gt;", text)
        keyboard = msg_answer.call_args.kwargs["reply_markup"].inline_keyboard
        self.assertEqual(keyboard[0][0].url, "https://t.me/kanal")
        self.assertEqual(keyboard[1][0].callback_data, "sub_check")

    async def test_subscribed_or_backend_error_passes(self):
        for gate in ({"required": False}, ApiXato("server_ga_ulab_bolmadi", "down")):
            result, handler, *_ = await self.run_mw(make_message("salom"), gate)
            self.assertEqual(result, "handled")
            handler.assert_called_once()

    async def test_staff_link_and_groups_skip_check(self):
        for event in (make_message("/start staff_abc"), make_message("/ulash abc"), make_message("hi", "group")):
            result, handler, api_call, *_ = await self.run_mw(event, GATE)
            self.assertEqual(result, "handled")
            api_call.assert_not_called()

    async def test_check_button(self):
        _, handler, api_call, _, cb_answer, _ = await self.run_mw(make_callback("sub_check"), GATE)
        handler.assert_not_called()
        self.assertTrue(api_call.call_args.kwargs["fresh"])
        self.assertTrue(cb_answer.call_args.kwargs["show_alert"])

        _, handler, _, msg_answer, _, _ = await self.run_mw(make_callback("sub_check"), {"required": False})
        handler.assert_not_called()
        self.assertIn("/start", msg_answer.call_args.args[0])

    async def test_other_button_blocked_when_unsubscribed(self):
        _, handler, _, _, _, send = await self.run_mw(make_callback("menu:x"), GATE)
        handler.assert_not_called()
        self.assertEqual(send.call_args.args[0], 42)


class StaffLinkHandlerTest(unittest.IsolatedAsyncioTestCase):
    async def test_sends_code_and_telegram_id(self):
        state = AsyncMock()
        with patch.object(
            staff_link.api, "staff_link", AsyncMock(return_value={"linked": True, "message": "✅ ok"})
        ) as call, patch.object(Message, "answer", AsyncMock()) as answer:
            await staff_link.staff_link(make_message("/start staff_CODE-1"), state)
        call.assert_awaited_once_with("CODE-1", 42)
        answer.assert_awaited_once_with("✅ ok")
        state.clear.assert_awaited()


if __name__ == "__main__":
    unittest.main()
