from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class LoginIdentifierTest(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user(username="12345678901234", password="Parol12345!")
        User.objects.create_user(username="+998901112233", password="Parol12345!")
        User.objects.create_user(username="Admin", password="Parol12345!", telefon="+998907654321")

    def login(self, username):
        return APIClient().post("/api/auth/token/", {"username": username, "password": "Parol12345!"}, format="json")

    def test_long_numeric_username(self):
        self.assertEqual(self.login("12345678901234").status_code, 200)
        self.assertEqual(self.login(" 12345678901234 ").status_code, 200)

    def test_phone_in_any_format(self):
        for raw in ("+998 90 111 22 33", "998901112233", "901112233", "0901112233"):
            self.assertEqual(self.login(raw).status_code, 200, raw)

    def test_username_case_and_phone_field(self):
        self.assertEqual(self.login("admin").status_code, 200)
        self.assertEqual(self.login("90 765 43 21").status_code, 200)

    def test_unknown_login_message(self):
        res = self.login("nobody")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["error"], "login_topilmadi")
