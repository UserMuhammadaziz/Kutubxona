from datetime import date, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from berish.models import Berish
from berish.services import kitob_qaytar
from kitob.models import Kitob
from oquvchi.models import Oquvchi
from organization.models import Membership, Organization
from telegrambot.handler import handle_update
from telegrambot.models import TelegramBot

from .models import Review

User = get_user_model()
TOKEN = "123456:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789"


class Base(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(nomi="Asosiy", status=Organization.HOLAT_ACTIVE)
        self.librarian = User.objects.create_user(username="lib", password="parol12345")
        Membership.objects.create(organization=self.org, user=self.librarian, rol="kutubxonachi")
        self.book = Kitob.objects.create(
            organization=self.org, nomi="O'tkan kunlar", muallif="Abdulla Qodiriy", janr="badiiy", nashr_yili=2015
        )
        self.reader = Oquvchi.objects.create(
            organization=self.org, fish="Karimov Alisher", telefon="+998901234567", karta_raqami="K1",
            telegram_id=111, sinf="9-A",
        )
        self.other = Oquvchi.objects.create(
            organization=self.org, fish="Raximova Shoxista", telefon="+998902345678", karta_raqami="K2",
            telegram_id=222,
        )
        self.bot = TelegramBot(
            organization=self.org, telegram_bot_id=123456, username="asosiy_bot",
            webhook_path=TelegramBot.yangi_webhook_path(), webhook_secret=TelegramBot.yangi_secret(),
            holati="ulangan",
        )
        self.bot.set_token(TOKEN)
        self.bot.save()

    def loan(self, reader, returned=True):
        return Berish.objects.create(
            organization=self.org, kitob=self.book, oquvchi=reader,
            berilgan_sana=date.today() - timedelta(days=10), qaytarish_muddati=date.today() + timedelta(days=5),
            qaytarilgan_sana=date.today() if returned else None, holati="qaytarilgan" if returned else "faol",
        )


@override_settings(BOT_SERVICE_USERNAME="botservice")
class BotApiTest(Base):
    def setUp(self):
        super().setUp()
        self.bot.polling = True
        self.bot.save()
        self.service = APIClient()
        self.service.force_authenticate(User.objects.create_user(username="botservice", password="parol12345"))

    def get(self, telegram_id):
        return self.service.get("/api/reviews/bot/", {"book": self.book.pk, "telegram_id": telegram_id}, HTTP_X_BOT_ID="123456")

    def post(self, telegram_id, **body):
        payload = {"book": self.book.pk, "telegram_id": telegram_id, **body}
        return self.service.post("/api/reviews/bot/", payload, format="json", HTTP_X_BOT_ID="123456")

    def test_only_readers_who_returned_the_book_can_review(self):
        self.assertFalse(self.get(111).data["can_review"])
        self.assertEqual(self.post(111, rating=5).status_code, 403)
        self.loan(self.reader, returned=False)
        self.assertEqual(self.post(111, rating=5).status_code, 403)  # still reading
        self.loan(self.reader)
        self.assertTrue(self.get(111).data["can_review"])
        self.assertEqual(self.post(111, rating=6).status_code, 400)
        response = self.post(111, rating=4, text="Juda ta'sirli roman")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["author"], "Alisher (9-A)")  # no full name
        # Writing again edits the same review.
        self.post(111, rating=5, text="Qayta o'qidim")
        self.assertEqual(Review.objects.count(), 1)
        data = self.get(222).data
        self.assertEqual(data["summary"], {"avg": 5.0, "count": 1})
        self.assertEqual(data["reviews"][0]["text"], "Qayta o'qidim")
        self.assertIsNone(data["mine"])
        self.assertEqual(self.get(111).data["mine"], {"rating": 5, "text": "Qayta o'qidim"})

    def test_book_detail_carries_rating(self):
        self.loan(self.reader)
        self.post(111, rating=4)
        self.loan(self.other)
        self.post(222, rating=5)
        staff = APIClient()
        staff.force_authenticate(self.librarian)
        data = staff.get(f"/api/books/{self.book.pk}/", HTTP_X_ORGANIZATION_ID=str(self.org.pk)).data
        self.assertEqual(data["rating"], {"avg": 4.5, "count": 2})

    def test_unknown_bot_and_plain_users_are_refused(self):
        response = self.service.get("/api/reviews/bot/", {"book": self.book.pk, "telegram_id": 111}, HTTP_X_BOT_ID="999")
        self.assertEqual(response.status_code, 400)
        plain = APIClient()
        plain.force_authenticate(self.librarian)
        self.assertEqual(plain.get("/api/reviews/bot/", {"book": self.book.pk}).status_code, 403)


class StaffApiTest(Base):
    def test_list_and_hide(self):
        self.loan(self.reader)
        review = Review.objects.create(organization=self.org, book=self.book, reader=self.reader, rating=1, text="yomon")
        client = APIClient()
        client.force_authenticate(self.librarian)
        data = client.get("/api/reviews/", {"book": self.book.pk}, HTTP_X_ORGANIZATION_ID=str(self.org.pk)).data
        self.assertEqual(data["results"][0]["reader_name"], "Karimov Alisher")
        response = client.post(f"/api/reviews/{review.pk}/hide/", {"hidden": True}, format="json",
                               HTTP_X_ORGANIZATION_ID=str(self.org.pk))
        self.assertTrue(response.data["is_hidden"])
        from .services import summary

        self.assertEqual(summary(self.book)["count"], 0)

    def test_other_library_cannot_see(self):
        other_org = Organization.objects.create(nomi="Boshqa", status=Organization.HOLAT_ACTIVE)
        stranger = User.objects.create_user(username="x", password="parol12345")
        Membership.objects.create(organization=other_org, user=stranger, rol="kutubxonachi")
        client = APIClient()
        client.force_authenticate(stranger)
        response = client.get("/api/reviews/", {"book": self.book.pk}, HTTP_X_ORGANIZATION_ID=str(other_org.pk))
        self.assertEqual(response.status_code, 404)


class WebhookFlowTest(Base):
    def setUp(self):
        super().setUp()
        sender = mock.patch("telegrambot.handler.xabar_yubor", return_value=True)
        self.send = sender.start()
        self.addCleanup(sender.stop)
        answer = mock.patch("telegrambot.handler.answer_callback_query")
        answer.start()
        self.addCleanup(answer.stop)

    def callback(self, data, telegram_id=111):
        handle_update(self.bot, {"callback_query": {"id": "c", "from": {"id": telegram_id}, "data": data,
                                                     "message": {"chat": {"id": telegram_id}}}})

    def text(self, text, telegram_id=111):
        handle_update(self.bot, {"message": {"chat": {"id": telegram_id, "type": "private"},
                                             "from": {"id": telegram_id}, "text": text}})

    def last(self):
        return self.send.call_args.args[2]

    def test_rate_then_write(self):
        self.callback(f"rv_new:{self.book.pk}")
        self.assertIn("qaytargandan keyin", self.last())
        self.loan(self.reader)
        self.callback(f"kitob:{self.book.pk}")
        buttons = [b["callback_data"] for row in self.send.call_args.kwargs.get("reply_markup", self.send.call_args.args[3] if len(self.send.call_args.args) > 3 else {})["inline_keyboard"] for b in row]
        self.assertIn(f"rv_new:{self.book.pk}", buttons)
        self.callback(f"rv_rate:{self.book.pk}:4")
        self.text("Tarixiy roman, hammaga tavsiya qilaman")
        review = Review.objects.get()
        self.assertEqual((review.rating, review.text), (4, "Tarixiy roman, hammaga tavsiya qilaman"))
        self.assertIn("saqlandi", self.last())
        self.callback(f"rv_list:{self.book.pk}", telegram_id=222)
        self.assertIn("Tarixiy roman", self.last())
        self.assertNotIn("Karimov", self.last())

    def test_skip_text(self):
        self.loan(self.reader)
        self.callback(f"rv_rate:{self.book.pk}:5")
        self.callback(f"rv_skip:{self.book.pk}:5")
        self.assertEqual(Review.objects.get().text, "")


class ReturnInviteTest(Base):
    def test_reader_is_asked_to_rate_after_return(self):
        loan = self.loan(self.reader, returned=False)
        with mock.patch("config.telegram.telegram_xabar_yubor") as send, self.captureOnCommitCallbacks(execute=True):
            kitob_qaytar(loan, self.librarian)
        calls = [c for c in send.call_args_list if c.kwargs.get("reply_markup")]
        markup = calls[-1].kwargs["reply_markup"]
        self.assertEqual(markup["inline_keyboard"][0][0]["callback_data"], f"rv_rate:{self.book.pk}:1")
