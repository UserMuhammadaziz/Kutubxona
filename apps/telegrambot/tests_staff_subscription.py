"""Staff Telegram linking from the profile and mandatory channel subscription."""

from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from oquvchi.models import Oquvchi
from organization.models import Membership, Organization

from .client import TelegramAPIError
from .handler import handle_update
from .models import TelegramBot

User = get_user_model()
TOKEN = "123456:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789"
CHANNEL = {"id": -1001234567890, "type": "channel", "title": "Kutubxona yangiliklari", "username": "kutub_news"}


def member(status, **extra):
    return {"status": status, **extra}


class Base(TestCase):
    def setUp(self):
        cache.clear()
        self.org = Organization.objects.create(nomi="Asosiy", status=Organization.HOLAT_ACTIVE)
        self.user = User.objects.create_user(username="lib", password="parol12345", full_name="Ali <Valiyev>")
        self.membership = Membership.objects.create(organization=self.org, user=self.user, rol="egasi")
        self.bot = TelegramBot(
            organization=self.org,
            telegram_bot_id=123456,
            username="asosiy_bot",
            webhook_path=TelegramBot.yangi_webhook_path(),
            webhook_secret=TelegramBot.yangi_secret(),
            holati="ulangan",
        )
        self.bot.set_token(TOKEN)
        self.bot.save()
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        sender = mock.patch("telegrambot.handler.xabar_yubor", return_value=True)
        self.send = sender.start()
        self.addCleanup(sender.stop)

    def message(self, text, telegram_id=777):
        return {"message": {"chat": {"id": telegram_id, "type": "private"}, "from": {"id": telegram_id}, "text": text}}

    def sent_texts(self):
        return [c.args[2] for c in self.send.call_args_list]


class StaffLinkTest(Base):
    def test_profile_link_flow_via_deep_link(self):
        status = self.client.get("/api/organizations/telegram-link-status/").data
        self.assertEqual(status, {"linked": False, "bot_username": "asosiy_bot"})

        data = self.client.post("/api/organizations/telegram-link-code/").data
        self.assertEqual(data["deep_link"], f"https://t.me/asosiy_bot?start=staff_{data['code']}")
        self.assertLessEqual(len("staff_" + data["code"]), 64)  # Telegram start payload limit

        handle_update(self.bot, self.message(f"/start staff_{data['code']}"))
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.telegram_id, 777)
        self.assertEqual(self.membership.link_code, "")
        self.assertIn("Ali &lt;Valiyev&gt;", self.sent_texts()[-1])
        self.assertTrue(self.client.get("/api/organizations/telegram-link-status/").data["linked"])

        # The code is single use.
        handle_update(self.bot, self.message(f"/start staff_{data['code']}", telegram_id=888))
        self.assertIn("yaroqsiz", self.sent_texts()[-1])

        self.client.post("/api/organizations/telegram-unlink/")
        self.membership.refresh_from_db()
        self.assertIsNone(self.membership.telegram_id)

    def test_ulash_command_still_works(self):
        code = self.membership.yangi_link_kod()
        handle_update(self.bot, self.message(f"/ulash {code}"))
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.telegram_id, 777)

    def test_telegram_account_used_by_other_staff(self):
        other = User.objects.create_user(username="lib2", password="parol12345")
        Membership.objects.create(organization=self.org, user=other, rol="kutubxonachi", telegram_id=777)
        code = self.membership.yangi_link_kod()
        handle_update(self.bot, self.message(f"/start staff_{code}"))
        self.membership.refresh_from_db()
        self.assertIsNone(self.membership.telegram_id)
        self.assertIn("boshqa xodimga", self.sent_texts()[-1])

    def test_link_code_needs_connected_bot(self):
        self.bot.holati = "uzilgan"
        self.bot.save()
        response = self.client.post("/api/organizations/telegram-link-code/")
        self.assertEqual(response.status_code, 400)


@override_settings(BOT_SERVICE_USERNAME="botservice")
class PollingBotApiTest(Base):
    def setUp(self):
        super().setUp()
        self.bot.polling = True
        self.bot.save()
        self.service = APIClient()
        self.service.force_authenticate(User.objects.create_user(username="botservice", password="parol12345"))

    def test_staff_link_endpoint(self):
        code = self.membership.yangi_link_kod()
        response = self.service.post(
            "/api/telegram/bot/staff-link/", {"code": code, "telegram_id": 555}, format="json", HTTP_X_BOT_ID="123456"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["linked"])
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.telegram_id, 555)

    def test_only_service_account_and_known_bot(self):
        code = self.membership.yangi_link_kod()
        payload = {"code": code, "telegram_id": 555}
        response = self.client.post("/api/telegram/bot/staff-link/", payload, format="json", HTTP_X_BOT_ID="123456")
        self.assertEqual(response.status_code, 403)
        response = self.service.post("/api/telegram/bot/staff-link/", payload, format="json", HTTP_X_BOT_ID="999")
        self.assertEqual(response.status_code, 400)

    def test_subscription_endpoint(self):
        Organization.objects.filter(pk=self.org.pk).update(
            subscription_channel_id=CHANNEL["id"], subscription_channel_title="Kanal", subscription_channel_url="https://t.me/x"
        )
        with mock.patch("telegrambot.subscription.get_chat_member", return_value=member("left")):
            response = self.service.get("/api/telegram/bot/subscription/", {"telegram_id": 42}, HTTP_X_BOT_ID="123456")
        self.assertEqual(response.data, {"required": True, "title": "Kanal", "url": "https://t.me/x"})
        with mock.patch("telegrambot.subscription.get_chat_member", return_value=member("member")):
            response = self.service.get(
                "/api/telegram/bot/subscription/", {"telegram_id": 42, "fresh": "1"}, HTTP_X_BOT_ID="123456"
            )
        self.assertEqual(response.data, {"required": False})


class SubscriptionChannelSettingTest(Base):
    def put(self, channel):
        return self.client.post(f"/api/organizations/{self.org.pk}/subscription-channel/", {"channel": channel}, format="json")

    @mock.patch("telegrambot.subscription.get_me", return_value={"id": 123456, "username": "asosiy_bot"})
    @mock.patch("telegrambot.subscription.get_chat", return_value=CHANNEL)
    def test_save_requires_bot_admin(self, get_chat, get_me):
        with mock.patch("telegrambot.subscription.get_chat_member", return_value=member("member")):
            response = self.put("https://t.me/kutub_news")
        self.assertEqual(response.status_code, 400)
        self.assertIn("administrator emas", str(response.data))
        get_chat.assert_called_with(TOKEN, "@kutub_news")

        with mock.patch("telegrambot.subscription.get_chat_member", return_value=member("administrator")):
            response = self.put("@kutub_news")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["subscription_channel_url"], "https://t.me/kutub_news")
        self.org.refresh_from_db()
        self.assertEqual(self.org.subscription_channel_id, CHANNEL["id"])

        response = self.client.delete(f"/api/organizations/{self.org.pk}/subscription-channel/")
        self.assertEqual(response.status_code, 200)
        self.org.refresh_from_db()
        self.assertIsNone(self.org.subscription_channel_id)

    def test_bad_input_and_unknown_channel(self):
        self.assertEqual(self.put("a b").status_code, 400)
        self.assertEqual(self.put("").status_code, 400)
        with mock.patch("telegrambot.subscription.get_chat", side_effect=TelegramAPIError("getChat", "chat not found")):
            response = self.put("@missing_channel")
        self.assertEqual(response.status_code, 400)
        self.assertIn("topilmadi", str(response.data))

    def test_librarian_cannot_change(self):
        self.membership.rol = "kutubxonachi"
        self.membership.save()
        self.assertEqual(self.put("@kutub_news").status_code, 403)


class SubscriptionGateTest(Base):
    def setUp(self):
        super().setUp()
        Organization.objects.filter(pk=self.org.pk).update(
            subscription_channel="@kutub_news",
            subscription_channel_id=CHANNEL["id"],
            subscription_channel_title="Kutubxona yangiliklari",
            subscription_channel_url="https://t.me/kutub_news",
        )
        self.bot.refresh_from_db()
        Oquvchi.objects.create(organization=self.org, fish="Vali Aliyev", telefon="+998901112233", karta_raqami="K1", telegram_id=777)

    def test_unsubscribed_reader_is_stopped_then_let_in(self):
        with mock.patch("telegrambot.subscription.get_chat_member", return_value=member("left")):
            handle_update(self.bot, self.message("/start"))
        self.assertIn("obuna bo'ling", self.sent_texts()[-1])
        keyboard = self.send.call_args.kwargs["reply_markup"]["inline_keyboard"]
        self.assertEqual(keyboard[0][0]["url"], "https://t.me/kutub_news")

        callback = {"callback_query": {"id": "c1", "from": {"id": 777}, "data": "sub_check"}}
        with mock.patch("telegrambot.subscription.get_chat_member", return_value=member("left")), mock.patch(
            "telegrambot.handler.answer_callback_query"
        ) as answer:
            handle_update(self.bot, callback)
        self.assertIn("obuna bo'lmagansiz", answer.call_args.args[2])

        with mock.patch("telegrambot.subscription.get_chat_member", return_value=member("member")), mock.patch(
            "telegrambot.handler.answer_callback_query"
        ):
            handle_update(self.bot, callback)
        self.assertIn("Xush kelibsiz", self.sent_texts()[-1])

        # A positive answer is cached, so Telegram is not asked again right away.
        with mock.patch("telegrambot.subscription.get_chat_member") as check:
            handle_update(self.bot, self.message("/yordam"))
        check.assert_not_called()

    def test_staff_exempt_and_fail_open(self):
        self.membership.telegram_id = 777
        self.membership.save()
        with mock.patch("telegrambot.subscription.get_chat_member") as check:
            handle_update(self.bot, self.message("/start"))
        check.assert_not_called()

        self.membership.telegram_id = None
        self.membership.save()
        with mock.patch(
            "telegrambot.subscription.get_chat_member", side_effect=TelegramAPIError("getChatMember", "Forbidden")
        ):
            handle_update(self.bot, self.message("/start"))
        self.assertNotIn("obuna bo'ling", self.sent_texts()[-1])

    def test_staff_link_not_blocked_by_gate(self):
        code = self.membership.yangi_link_kod()
        with mock.patch("telegrambot.subscription.get_chat_member", return_value=member("left")):
            handle_update(self.bot, self.message(f"/start staff_{code}", telegram_id=999))
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.telegram_id, 999)
