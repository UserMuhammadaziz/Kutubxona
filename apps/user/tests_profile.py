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
