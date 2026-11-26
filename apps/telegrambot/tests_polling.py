"""The server's polling bot linked to a library: sends, but never gets a webhook."""
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from config.telegram import _token_ol
from organization.models import Organization
from telegrambot import services
from telegrambot.models import TelegramBot

TOKEN = "123456789:" + "A" * 35
ME = {"id": 123456789, "username": "kutubxonaschoolbot"}


@override_settings(TELEGRAM_BOT_TOKEN=TOKEN, TELEGRAM_WEBHOOK_BASE_URL="https://example.test")
class PollingBotTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(nomi="Asosiy", slug="asosiy-kutubxona", status=Organization.HOLAT_ACTIVE)
        self.other = Organization.objects.create(nomi="Boshqa", slug="boshqa", status=Organization.HOLAT_ACTIVE)

    def link(self):
        with patch("telegrambot.services.get_me", return_value=ME), patch("telegrambot.services.set_webhook") as hook:
            call_command("link_polling_bot", "asosiy-kutubxona", stdout=open("/dev/null", "w"))
        hook.assert_not_called()
        return TelegramBot.objects.get(organization=self.org)

    def test_link_stores_token_without_webhook(self):
        bot = self.link()
        self.assertTrue(bot.polling)
        self.assertEqual(bot.holati, "ulangan")
        self.assertFalse(bot.webhook_ornatilgan)
        self.assertEqual(bot.get_token(), TOKEN)

    def test_token_used_even_with_many_active_libraries(self):
        # Two active libraries: the old global fallback would refuse.
        self.assertEqual(_token_ol(organization=self.org), "")
        self.link()
        self.org.refresh_from_db()
        self.assertEqual(_token_ol(organization=self.org), TOKEN)
        self.assertEqual(_token_ol(organization=self.other), "")

    def test_webhook_actions_never_touch_polling_bot(self):
        bot = self.link()
        with patch("telegrambot.services.set_webhook") as set_hook, patch("telegrambot.services.delete_webhook") as del_hook, patch(
            "telegrambot.services.get_me", return_value=ME
        ), patch("telegrambot.services.get_webhook_info") as info:
            services.webhookni_qayta_ornat(bot)
            services.botni_tekshirish(bot)
            with patch("telegrambot.services.get_me", return_value=ME):
                services.botni_ulash(self.org, TOKEN)
        set_hook.assert_not_called()
        del_hook.assert_not_called()
        info.assert_not_called()
        bot.refresh_from_db()
        self.assertTrue(bot.polling)
        self.assertEqual(bot.holati, "ulangan")

    def test_same_bot_cannot_go_to_another_library(self):
        self.link()
        with patch("telegrambot.services.get_me", return_value=ME):
            with self.assertRaises(Exception):
                services.link_polling_bot(self.other, TOKEN)
