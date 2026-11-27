"""Webhook mode: updates arrive over HTTP and need the secret header.

Run from `bot/`: python -m unittest tests.test_webhook
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import aiohttp
from aiogram import Bot, Dispatcher

import config
import main

PORT = 18081


class WebhookTest(unittest.IsolatedAsyncioTestCase):
    async def test_secret_is_required_and_update_is_dispatched(self):
        bot = Bot("123456:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789")
        dp = Dispatcher()
        seen = []

        @dp.message()
        async def echo(message):
            seen.append(message.text)

        settings = {
            "WEBHOOK_URL": "https://example.test/tg/hook-path",
            "WEBHOOK_SECRET": "s3cret",
            "WEBHOOK_HOST": "127.0.0.1",
            "WEBHOOK_PORT": PORT,
        }
        with patch.multiple(config, **settings), patch.object(Bot, "set_webhook", AsyncMock()) as set_webhook:
            server = asyncio.create_task(main._serve_webhook(bot, dp))
            await asyncio.sleep(0.3)
            update = {
                "update_id": 1,
                "message": {
                    "message_id": 1,
                    "date": 0,
                    "chat": {"id": 7, "type": "private"},
                    "from": {"id": 7, "is_bot": False, "first_name": "A"},
                    "text": "salom",
                },
            }
            url = f"http://127.0.0.1:{PORT}/tg/hook-path"
            async with aiohttp.ClientSession() as http:
                async with http.post(url, json=update, headers={"X-Telegram-Bot-Api-Secret-Token": "bad"}) as r:
                    self.assertEqual(r.status, 401)
                async with http.post(url, json=update, headers={"X-Telegram-Bot-Api-Secret-Token": "s3cret"}) as r:
                    self.assertEqual(r.status, 200)
            await asyncio.sleep(0.2)
            server.cancel()
            await asyncio.gather(server, return_exceptions=True)
        await bot.session.close()
        self.assertEqual(seen, ["salom"])
        set_webhook.assert_awaited_once()
        self.assertEqual(set_webhook.call_args.kwargs["secret_token"], "s3cret")


if __name__ == "__main__":
    unittest.main()
