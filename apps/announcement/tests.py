from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from oquvchi.models import Oquvchi

from . import services
from .models import Announcement

User = get_user_model()


class AnnouncementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="lib", password="parol12345", full_name="Lib", rol="kutubxonachi"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        Oquvchi.objects.create(fish="A", telefon="+998900000001", telegram_id=1)
        Oquvchi.objects.create(fish="B", telefon="+998900000002")

    def test_preview_counts_only_telegram_readers(self):
        res = self.client.post("/api/announcements/preview/", {"audience": "all"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["recipients"], 1)

    @patch("announcement.services.xabar_yubor", return_value=True)
    def test_send_logs_counts(self, _send):
        res = self.client.post(
            "/api/announcements/send/", {"audience": "all", "text": "Chegirma!"}, format="json"
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["sent_count"], 1)
        self.assertEqual(Announcement.objects.count(), 1)

    @patch("announcement.services.xabar_yubor", return_value=True)
    def test_daily_limit(self, _send):
        for _ in range(services.DAILY_LIMIT):
            self.client.post("/api/announcements/send/", {"audience": "all", "text": "x"}, format="json")
        res = self.client.post("/api/announcements/send/", {"audience": "all", "text": "x"}, format="json")
        self.assertEqual(res.status_code, 400)
