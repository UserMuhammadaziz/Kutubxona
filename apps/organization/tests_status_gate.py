"""Non-active organizations: the API must give the client what the status screen needs."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from organization.models import Membership, Organization


class OrganizationStatusGateTests(TestCase):
    BLOCKED = ("pending", "suspended", "rejected", "archived")

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="owner", password="StrongPass123")
        self.org = Organization.objects.create(nomi="Gate library", slug="gate-library")
        Membership.objects.create(user=self.user, organization=self.org, rol="egasi", faol=True)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _set(self, status):
        Organization.objects.filter(pk=self.org.pk).update(status=status, status_reason="Reason")

    def test_me_exposes_status_of_each_library(self):
        for status in (*self.BLOCKED, "active"):
            self._set(status)
            res = self.client.get("/api/auth/me/")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.data["kutubxonalar"][0]["status"], status)

    def test_tenant_endpoints_return_machine_readable_code(self):
        for status in self.BLOCKED:
            self._set(status)
            for headers in ({}, {"HTTP_X_ORGANIZATION_ID": str(self.org.pk)}):
                for url in ("/api/books/", "/api/loans/", "/api/stats/dashboard/"):
                    res = self.client.get(url, **headers)
                    self.assertEqual(res.status_code, 403, (status, url))
                    self.assertEqual(res.json()["error"], f"organization_{status}", url)

    def test_user_without_any_library_gets_its_own_code(self):
        Membership.objects.all().update(faol=False)
        res = self.client.get("/api/books/")
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["error"], "organization_none")
        self.assertIs(self.client.get("/api/auth/me/").data["no_organization"], True)

    def test_member_is_not_marked_as_without_library(self):
        self._set("pending")
        self.assertIs(self.client.get("/api/auth/me/").data["no_organization"], False)

    @override_settings(SUPPORT_PHONE="+998000000000", SUPPORT_TELEGRAM="support_test")
    def test_status_endpoint_works_while_blocked(self):
        for status in self.BLOCKED:
            self._set(status)
            res = self.client.get("/api/auth/organization/")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.data["status"], status)
            self.assertEqual(res.data["status_reason"], "Reason")
            self.assertEqual(
                res.data["support"], {"phone": "+998000000000", "telegram": "support_test"}
            )

    def test_blocked_owner_can_message_the_platform(self):
        self._set("suspended")
        res = self.client.post(
            "/api/issue-reports/",
            {"category": "other", "module": "organization", "message": "Why?"},
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)

    def test_freeze_and_unfreeze_by_platform_admin(self):
        admin = get_user_model().objects.create_superuser(username="root", password="x")
        platform = APIClient()
        platform.force_authenticate(admin)
        url = f"/api/saas/organizations/{self.org.pk}"
        self._set("active")
        self.assertEqual(self.client.get("/api/books/").status_code, 200)
        res = platform.post(f"{url}/suspend/", {"reason": "Payment"}, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(self.client.get("/api/books/").json()["error"], "organization_suspended")
        res = platform.post(f"{url}/activate/", {}, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(self.client.get("/api/books/").status_code, 200)
