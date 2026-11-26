"""Platform organization card: /api/saas/organizations/<id>/details/."""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from marketing.models import SignupAttribution, Visit
from organization.models import AuditLog, Membership, Organization

User = get_user_model()


class PlatformDetailsTest(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(username="+998901112233", full_name="Ali Valiyev", telefon="+998901112233", password="x")
        self.org = Organization.objects.create(nomi="Yangi maktab", slug="yangi", status=Organization.HOLAT_PENDING, egasi=self.owner)
        Membership.objects.create(organization=self.org, user=self.owner, rol="egasi", faol=True)
        AuditLog.objects.create(organization=self.org, actor=self.owner, action="organization.registration_requested", metadata={"nomi": "Yangi maktab"})
        Visit.objects.create(visitor_id="visitor-0001", source="telegram", medium="social", landing_path="/")
        Visit.objects.create(visitor_id="visitor-0001", source="google", medium="cpc", campaign="noyabr", landing_path="/register")
        Visit.objects.create(visitor_id="someone-else", source="yandex", medium="organic")
        SignupAttribution.objects.create(organization=self.org, visitor_id="visitor-0001", source="telegram", medium="social", last_source="google", last_medium="cpc", last_campaign="noyabr")
        self.admin = APIClient()
        self.admin.force_authenticate(User.objects.create_user(username="root", password="x", is_staff=True))
        self.url = f"/api/saas/organizations/{self.org.pk}/details/"

    def test_card_has_owner_source_journey_and_history(self):
        res = self.admin.get(self.url)
        self.assertEqual(res.status_code, 200, res.content)
        data = res.json()
        self.assertEqual(data["organization"]["status"], "pending")
        self.assertEqual(data["owner"]["full_name"], "Ali Valiyev")
        self.assertEqual([m["role"] for m in data["members"]], ["egasi"])
        self.assertEqual(data["attribution"]["first"]["source"], "telegram")
        self.assertEqual(data["attribution"]["last"]["campaign"], "noyabr")
        self.assertEqual([v["source"] for v in data["attribution"]["visits"]], ["telegram", "google"])
        self.assertEqual(data["timeline"][0]["action"], "organization.registration_requested")
        self.assertEqual(data["usage"]["books"], 0)

    def test_without_attribution(self):
        SignupAttribution.objects.all().delete()
        self.assertIsNone(self.admin.get(self.url).json()["attribution"])

    def test_platform_only(self):
        owner = APIClient()
        owner.force_authenticate(self.owner)
        self.assertEqual(owner.get(self.url).status_code, 403)
        self.assertEqual(APIClient().get(self.url).status_code, 401)
