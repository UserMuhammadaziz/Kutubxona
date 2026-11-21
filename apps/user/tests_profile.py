"""Profil sahifasidagi parol almashtirish API testlari."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

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
