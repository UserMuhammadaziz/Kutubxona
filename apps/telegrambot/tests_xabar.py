"""Profil sahifasidagi «Kitobxonlarga xabar yuborish» API testlari.

Telegram tarmoqqa chiqmasligi uchun `telegram_xabar_yubor` mock qilinadi.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from config.test_helpers import TenantTestMixin
from oquvchi.models import Oquvchi

User = get_user_model()


class XabarYuborishTest(TenantTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.xodim = User.objects.create_user(
            username="kutubxonachi",
            password="parol12345",
            full_name="K",
            rol="kutubxonachi",
        )
        self.azolik(self.xodim)
        self.client.force_authenticate(self.xodim)

        self.ali = Oquvchi.objects.create(
            fish="Ali Valiyev", telefon="+998901111111", telegram_id=111,
            karta_raqami="A1", sinf="7-A",
        )
        self.vali = Oquvchi.objects.create(
            fish="Vali Valiyev", telefon="+998902222222", telegram_id=222,
            karta_raqami="A2", sinf="7-A",
        )
        self.soli = Oquvchi.objects.create(
            fish="Soli Soliyev", telefon="+998903333333",
            karta_raqami="A3", sinf="9-B",
        )
        self.oqituvchi = Oquvchi.objects.create(
            fish="Matematika o'qituvchisi", telefon="+998904444444",
            telegram_id=444, karta_raqami="T1", rol="oqituvchi", kasb="Matematika",
        )

    def test_sinflar_rol_boyicha(self):
        javob = self.client.get("/api/messages/classes/", {"rol": "oquvchi"})
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.json(), ["7-A", "9-B"])

        javob = self.client.get("/api/messages/classes/", {"rol": "oqituvchi"})
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.json(), [])

    @patch("telegrambot.views.telegram_xabar_yubor", return_value=True)
    def test_bitta_oquvchiga(self, yuborish):
        javob = self.client.post(
            "/api/messages/send/",
            {"tur": "shaxs", "rol": "oquvchi", "oquvchi": self.ali.pk, "matn": "Salom"},
        )
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(
            javob.json(),
            {"jami": 1, "yuborildi": 1, "telegramsiz": 0, "xatolik": 0},
        )
        self.assertEqual(yuborish.call_count, 1)
        self.assertEqual(yuborish.call_args.args[0], 111)
        self.assertIn("Salom", yuborish.call_args.args[1])

    @patch("telegrambot.views.telegram_xabar_yubor", return_value=True)
    def test_sinfga_faqat_shu_sinf(self, yuborish):
        javob = self.client.post(
            "/api/messages/send/",
            {"tur": "sinf", "rol": "oquvchi", "sinf": "7-A", "matn": "Sinfga"},
        )
        self.assertEqual(javob.status_code, 200)
        natija = javob.json()
        self.assertEqual(natija["jami"], 2)
        self.assertEqual(natija["yuborildi"], 2)
        self.assertEqual(yuborish.call_count, 2)
        self.assertEqual(
            sorted(c.args[0] for c in yuborish.call_args_list), [111, 222]
        )

    @patch("telegrambot.views.telegram_xabar_yubor", return_value=True)
    def test_barcha_sinflarga_telegramsiz_ham_hisoblanadi(self, yuborish):
        javob = self.client.post(
            "/api/messages/send/",
            {"tur": "hamma", "rol": "oquvchi", "matn": "Hammaga"},
        )
        self.assertEqual(javob.status_code, 200)
        natija = javob.json()
        self.assertEqual(natija["jami"], 3)
        self.assertEqual(natija["yuborildi"], 2)
        self.assertEqual(natija["telegramsiz"], 1)
        self.assertEqual(natija["xatolik"], 0)
        self.assertEqual(yuborish.call_count, 2)

    @patch("telegrambot.views.telegram_xabar_yubor", return_value=True)
    def test_oqituvchilarga_alohida(self, yuborish):
        javob = self.client.post(
            "/api/messages/send/",
            {"tur": "hamma", "rol": "oqituvchi", "matn": "Hurmatli o'qituvchi"},
        )
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.json()["jami"], 1)
        self.assertEqual(yuborish.call_args.args[0], 444)

    @patch("telegrambot.views.telegram_xabar_yubor", return_value=False)
    def test_yuborish_xatosi_hisoblanadi(self, yuborish):
        javob = self.client.post(
            "/api/messages/send/",
            {"tur": "shaxs", "rol": "oquvchi", "oquvchi": self.ali.pk, "matn": "Salom"},
        )
        self.assertEqual(javob.json()["xatolik"], 1)
        self.assertEqual(javob.json()["yuborildi"], 0)

    def test_tanlov_shartlari(self):
        javob = self.client.post(
            "/api/messages/send/", {"tur": "shaxs", "rol": "oquvchi", "matn": "Salom"}
        )
        self.assertEqual(javob.status_code, 400)
        javob = self.client.post(
            "/api/messages/send/",
            {"tur": "sinf", "rol": "oquvchi", "sinf": "", "matn": "Salom"},
        )
        self.assertEqual(javob.status_code, 400)
        javob = self.client.post(
            "/api/messages/send/",
            {"tur": "shaxs", "rol": "oquvchi", "oquvchi": 99999, "matn": "Salom"},
        )
        self.assertEqual(javob.status_code, 400)

    def test_organization_siz_eski_kitobxonga_ham_yuboriladi(self):
        """Eski bot orqali yaratilgan, tashkilotga bog'lanmagan kitobxon."""
        eski = Oquvchi.objects.create(
            fish="Eski O'qituvchi", telefon="+998905555555", telegram_id=555,
            karta_raqami="T2", rol="oqituvchi", kasb="Tarix",
        )
        Oquvchi.objects.filter(pk=eski.pk).update(organization=None)

        with patch("telegrambot.views.telegram_xabar_yubor", return_value=True) as yuborish:
            javob = self.client.post(
                "/api/messages/send/",
                {"tur": "shaxs", "rol": "oqituvchi", "oquvchi": eski.pk, "matn": "Salom"},
            )
        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual(javob.json()["yuborildi"], 1)
        self.assertEqual(yuborish.call_args.args[0], 555)

    def test_boshqa_kutubxona_korinmaydi(self):
        from organization.models import Organization

        boshqa = Organization.objects.create(nomi="Boshqa kutubxona")
        Oquvchi.objects.create(
            organization=boshqa,
            fish="Begona o'quvchi",
            telefon="+998905555555",
            telegram_id=555,
            karta_raqami="B1",
            sinf="11-A",
        )
        javob = self.client.get("/api/messages/classes/", {"rol": "oquvchi"})
        self.assertNotIn("11-A", javob.json())

        with patch("telegrambot.views.telegram_xabar_yubor", return_value=True) as yuborish:
            javob = self.client.post(
                "/api/messages/send/",
                {"tur": "sinf", "rol": "oquvchi", "sinf": "11-A", "matn": "Salom"},
            )
        self.assertEqual(javob.status_code, 400)
        yuborish.assert_not_called()


class TokenFallbackTest(TestCase):
    """Bot UI orqali ulanmagan kutubxonada .env tokeni ishlatilishi."""

    @override_settings(TELEGRAM_BOT_TOKEN="test-token")
    def test_bitta_kutubxonada_global_token_fallback(self):
        from config.telegram import _token_ol
        from organization.models import Organization

        org = Organization.objects.create(nomi="Yagona kutubxona")
        self.assertEqual(_token_ol(organization=org), "test-token")

    @override_settings(TELEGRAM_BOT_TOKEN="test-token")
    def test_kop_kutubxonada_global_token_ishlatilmaydi(self):
        from config.telegram import _token_ol
        from organization.models import Organization

        org1 = Organization.objects.create(nomi="Birinchi kutubxona")
        Organization.objects.create(nomi="Ikkinchi kutubxona")
        self.assertEqual(_token_ol(organization=org1), "")
