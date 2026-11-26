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


class StaffOwnerRoleTest(TestCase):
    def setUp(self):
        from organization.models import Membership, Organization

        cache.clear()
        self.Membership = Membership
        self.org = Organization.objects.create(nomi="Kutubxona", slug="lib2", status=Organization.HOLAT_ACTIVE)

    def api(self, role):
        user = User.objects.create_user(username=f"actor-{role}", password="x")
        self.Membership.objects.create(organization=self.org, user=user, rol=role, faol=True)
        client = APIClient()
        client.force_authenticate(user)
        client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.pk))
        return client

    def create(self, client, role):
        return client.post(
            "/api/staff/",
            {"username": f"new-{role}", "full_name": "Ali Valiyev", "rol": role, "telefon": "", "password": "Parol12345!x"},
            format="json",
        )

    def test_owner_can_add_co_owner(self):
        res = self.create(self.api("egasi"), "egasi")
        self.assertEqual(res.status_code, 201, res.data)
        membership = self.Membership.objects.get(user__username="new-egasi")
        self.assertEqual((membership.rol, membership.user.rol), ("egasi", "administrator"))

    def test_administrator_cannot_add_owner(self):
        self.assertEqual(self.create(self.api("administrator"), "egasi").status_code, 400)

    def test_roles_still_work(self):
        api = self.api("administrator")
        for role in ("administrator", "kutubxonachi"):
            self.assertEqual(self.create(api, role).status_code, 201)
            self.assertEqual(self.Membership.objects.get(user__username=f"new-{role}").rol, role)
