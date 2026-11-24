"""Profil sahifasidagi parol almashtirish va xatolik xabari API testlari."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from config.test_helpers import TenantTestMixin
from organization.models import Organization

from .models import XatolikXabari

User = get_user_model()

URL = "/api/auth/change-password/"


class ParolniAlmashtirishTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.xodim = User.objects.create_user(
            username="kutubxonachi",
            password="eskiParol123!",
            full_name="K",
            rol="kutubxonachi",
        )
        self.client.force_authenticate(self.xodim)

    def test_notogri_joriy_parol(self):
        javob = self.client.post(
            URL,
            {
                "joriy_parol": "notogriParol!",
                "yangi_parol": "yangiParol456!",
                "yangi_parol_takror": "yangiParol456!",
            },
        )
        self.assertEqual(javob.status_code, 400)
        self.xodim.refresh_from_db()
        self.assertTrue(self.xodim.check_password("eskiParol123!"))

    def test_parollar_mos_kelmadi(self):
        javob = self.client.post(
            URL,
            {
                "joriy_parol": "eskiParol123!",
                "yangi_parol": "yangiParol456!",
                "yangi_parol_takror": "boshqaParol456!",
            },
        )
        self.assertEqual(javob.status_code, 400)
        self.xodim.refresh_from_db()
        self.assertTrue(self.xodim.check_password("eskiParol123!"))

    def test_muvaffaqiyatli_almashtirish(self):
        javob = self.client.post(
            URL,
            {
                "joriy_parol": "eskiParol123!",
                "yangi_parol": "yangiParol456!",
                "yangi_parol_takror": "yangiParol456!",
            },
        )
        self.assertEqual(javob.status_code, 200)
        self.xodim.refresh_from_db()
        self.assertTrue(self.xodim.check_password("yangiParol456!"))
        self.assertFalse(self.xodim.check_password("eskiParol123!"))

    def test_autentifikatsiyasiz_rad_etiladi(self):
        self.client.force_authenticate(user=None)
        javob = self.client.post(
            URL,
            {
                "joriy_parol": "eskiParol123!",
                "yangi_parol": "yangiParol456!",
                "yangi_parol_takror": "yangiParol456!",
            },
        )
        self.assertEqual(javob.status_code, 401)


PROFIL_URL = "/api/auth/profile/"


class ShaxsiyMalumotlarniYangilashTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.xodim = User.objects.create_user(
            username="kutubxonachi",
            password="parol12345",
            full_name="Eski Ism",
            telefon="+998901111111",
            rol="kutubxonachi",
        )
        self.client.force_authenticate(self.xodim)

    def test_ism_va_telefon_yangilanadi(self):
        javob = self.client.patch(
            PROFIL_URL,
            {"full_name": "Yangi Ism", "telefon": "+998909999999"},
            format="json",
        )
        self.assertEqual(javob.status_code, 200, javob.data)
        self.xodim.refresh_from_db()
        self.assertEqual(self.xodim.full_name, "Yangi Ism")
        self.assertEqual(self.xodim.telefon, "+998909999999")
        self.assertEqual(javob.data["username"], self.xodim.username)

    def test_login_yangilanadi(self):
        javob = self.client.patch(PROFIL_URL, {"username": "yangi_login"}, format="json")
        self.assertEqual(javob.status_code, 200, javob.data)
        self.xodim.refresh_from_db()
        self.assertEqual(self.xodim.username, "yangi_login")

    def test_band_login_rad_etiladi(self):
        User.objects.create_user(
            username="band_login", password="parol12345", full_name="Boshqa"
        )
        javob = self.client.patch(PROFIL_URL, {"username": "BAND_LOGIN"}, format="json")
        self.assertEqual(javob.status_code, 400)
        self.xodim.refresh_from_db()
        self.assertEqual(self.xodim.username, "kutubxonachi")

    def test_bosh_parol_ozgarmaydi(self):
        javob = self.client.patch(
            PROFIL_URL, {"full_name": "Yangi", "password": "boshqaParol123!"}, format="json"
        )
        self.assertEqual(javob.status_code, 200, javob.data)
        self.xodim.refresh_from_db()
        self.assertTrue(self.xodim.check_password("parol12345"))

    def test_autentifikatsiyasiz_rad_etiladi(self):
        self.client.force_authenticate(user=None)
        javob = self.client.patch(PROFIL_URL, {"full_name": "Yangi"}, format="json")
        self.assertEqual(javob.status_code, 401)


XATO_URL = "/api/auth/xatolik-xabari/"


class XatolikXabariTest(TenantTestMixin, TestCase):
    """Profil orqali xatolik haqida xabar yuborish."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.xodim = User.objects.create_user(
            username="kutubxonachi",
            password="parol12345",
            full_name="Kutubxonachi",
            rol="kutubxonachi",
        )
        self.azolik(self.xodim)
        self.client.force_authenticate(self.xodim)
        self.yuborilganlar = []

    def xabar(self, matn="", **qoshimcha):
        return self.client.post(
            XATO_URL,
            {"matn": matn, "sahifa": "/profile", **qoshimcha},
            format="json",
        )

    def test_saqlanadi_va_adminlarga_yuboriladi(self):
        from organization.models import Membership

        admin = User.objects.create_user(
            username="egasi", password="parol12345", full_name="Egasi", rol="administrator"
        )
        Membership.objects.create(
            organization=self.org,
            user=admin,
            rol="egasi",
            faol=True,
            telegram_id=999001,
        )
        with patch(
            "config.telegram.telegram_xabar_yubor",
            side_effect=lambda chat_id, matn, **kwargs: self.yuborilganlar.append(
                (chat_id, matn)
            )
            or True,
        ):
            javob = self.xabar("Kitob berishda xatolik yuz berdi")
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertTrue(javob.data["saqlandi"])
        self.assertEqual(javob.data["telegramga_yuborildi"], 1)
        self.assertEqual(XatolikXabari.objects.count(), 1)
        xabar = XatolikXabari.objects.first()
        self.assertEqual(xabar.yuborgan, self.xodim)
        self.assertEqual(xabar.organization, self.org)
        self.assertEqual(xabar.sahifa, "/profile")
        self.assertIn("Kitob berishda xatolik", self.yuborilganlar[0][1])
        self.assertEqual(self.yuborilganlar[0][0], 999001)

    def test_bot_ulangan_bolmasa_ham_saqlanadi(self):
        javob = self.xabar("Xatolik", tur="avtomatik")
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertEqual(javob.data["telegramga_yuborildi"], 0)
        self.assertEqual(XatolikXabari.objects.first().tur, "avtomatik")

    def test_matnsiz_rad_etiladi(self):
        javob = self.xabar("   ")
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(XatolikXabari.objects.count(), 0)

    def test_notogri_tur_qoldaga_tushadi(self):
        javob = self.xabar("Xatolik", tur="notogri")
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertEqual(XatolikXabari.objects.first().tur, "qolda")

    def test_royxat_faqat_joriy_kutubxonadan(self):
        self.xabar("Birinchi")
        boshqa_org = Organization.objects.create(
            nomi="Boshqa kutubxona", status=Organization.HOLAT_ACTIVE
        )
        XatolikXabari.objects.create(
            organization=boshqa_org, matn="Boshqa kutubxona xati", yuborgan=self.xodim
        )
        javob = self.client.get(XATO_URL)
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(len(javob.data), 1)
        self.assertEqual(javob.data[0]["matn"], "Birinchi")

    def test_env_admin_chatlari_zaxira_qabul_qiluvchi(self):
        import os

        with patch.dict(os.environ, {"BOT_ADMIN_CHAT_IDS": "555111, 555222"}):
            with patch(
                "config.telegram.telegram_xabar_yubor",
                side_effect=lambda chat_id, matn, **kwargs: self.yuborilganlar.append(
                    (chat_id, matn)
                )
                or True,
            ):
                javob = self.xabar("Zaxira xabar")
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertEqual(javob.data["telegramga_yuborildi"], 2)
        self.assertEqual([c[0] for c in self.yuborilganlar], [555111, 555222])

    def test_autentifikatsiyasiz_rad_etiladi(self):
        self.client.force_authenticate(user=None)
        javob = self.xabar("Xatolik")
        self.assertEqual(javob.status_code, 401)

