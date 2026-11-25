"""Platform admin: tariff plans and organization subscriptions."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from organization.models import AuditLog, Organization, OrganizationSubscription, SubscriptionPlan
from organization.services import subscription_for

PLANS = "/api/saas/plans/"


class PlanTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="root", password="StrongPass123")
        self.client_api = APIClient()
        self.client_api.force_authenticate(self.admin)
        self.org = Organization.objects.create(nomi="1-maktab", slug="1-maktab")
        self.subscription = subscription_for(self.org)
        self.free = self.subscription.plan

    def create(self, **extra):
        payload = {"nomi": "Boshlang'ich plus", "narx_oylik": "99000", "max_staff": 5, **extra}
        return self.client_api.post(PLANS, payload, format="json")

    def subscribe(self, **payload):
        return self.client_api.post(
            f"/api/saas/organizations/{self.org.pk}/subscription/", payload, format="json"
        )

    def test_create_generates_code_and_order(self):
        res = self.create()
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["code"], "boshlangich-plus")
        self.assertIsNone(res.data["max_resources"])
        self.assertEqual(res.data["organization_count"], 0)
        self.assertGreater(res.data["tartib"], self.free.tartib)
        self.assertTrue(AuditLog.objects.filter(action="plan.created").exists())

    def test_list_follows_the_display_order(self):
        first = self.create(nomi="Standart").data["id"]
        second = self.create(nomi="Pro").data["id"]
        for pk, tartib in ((second, 1), (first, 2), (self.free.pk, 3)):
            self.client_api.patch(f"{PLANS}{pk}/", {"tartib": tartib}, format="json")
        rows = [p["id"] for p in self.client_api.get(PLANS).data]
        self.assertEqual(rows[-3:], [second, first, self.free.pk])

    def test_code_is_generated_for_names_without_latin_letters(self):
        first = self.create(nomi="Мактаб")
        second = self.create(nomi="Лицей")
        self.assertEqual([first.data["code"], second.data["code"]], ["tarif", "tarif-2"])

    def test_invalid_values_are_rejected(self):
        self.assertEqual(self.create(nomi=" ").status_code, 400)
        self.assertEqual(self.create(narx_oylik="-1").status_code, 400)
        self.assertEqual(self.create(max_staff=0).status_code, 400)
        self.assertEqual(self.create().status_code, 201)
        self.assertEqual(self.create(nomi="BOSHLANG'ICH PLUS").status_code, 400)

    def test_update_keeps_code(self):
        pk = self.create().data["id"]
        res = self.client_api.patch(f"{PLANS}{pk}/", {"narx_oylik": "120000", "max_staff": None}, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertIsNone(res.data["max_staff"])
        res = self.client_api.patch(f"{PLANS}{pk}/", {"code": "other"}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_default_plan_is_protected(self):
        url = f"{PLANS}{self.free.pk}/"
        self.assertEqual(self.client_api.patch(url, {"faol": False}, format="json").status_code, 400)
        self.assertEqual(self.client_api.delete(url).status_code, 409)

    def test_delete_only_when_unused(self):
        pk = self.create().data["id"]
        self.assertEqual(self.subscribe(plan="boshlangich-plus").status_code, 200)
        self.assertEqual(self.client_api.delete(f"{PLANS}{pk}/").status_code, 409)
        self.assertEqual(self.subscribe(plan="free").status_code, 200)
        self.assertEqual(self.client_api.delete(f"{PLANS}{pk}/").status_code, 204)
        self.assertFalse(SubscriptionPlan.objects.filter(pk=pk).exists())

    def test_inactive_plan_stays_with_its_organizations_only(self):
        pk = self.create().data["id"]
        self.subscribe(plan="boshlangich-plus")
        self.client_api.patch(f"{PLANS}{pk}/", {"faol": False}, format="json")
        self.assertEqual(self.subscribe(plan="boshlangich-plus", status="active").status_code, 200)
        self.subscribe(plan="free")
        self.assertEqual(self.subscribe(plan="boshlangich-plus").status_code, 404)

    def test_subscription_dates(self):
        end = timezone.now() + timedelta(days=30)
        res = self.subscribe(status="active", current_period_end=end.isoformat(), trial_ends_at=None)
        self.assertEqual(res.status_code, 200, res.data)
        sub = OrganizationSubscription.objects.get(organization=self.org)
        self.assertEqual((sub.status, sub.trial_ends_at), ("active", None))
        self.assertEqual(self.subscribe(current_period_end="tomorrow").status_code, 400)
        self.assertEqual(self.subscribe(status="unknown").status_code, 400)

    def test_stats_show_the_subscription(self):
        self.subscribe(status="active", current_period_end=(timezone.now() - timedelta(days=1)).isoformat())
        bare = Organization.objects.create(nomi="2-maktab", slug="2-maktab")
        rows = {o["id"]: o for o in self.client_api.get("/api/saas/organizations/stats/").data["tashkilotlar"]}
        self.assertEqual(rows[self.org.pk]["subscription"]["effective_status"], "expired")
        self.assertEqual(rows[self.org.pk]["subscription"]["plan"], "free")
        self.assertIsNone(rows[bare.pk]["subscription"])
        self.assertFalse(OrganizationSubscription.objects.filter(organization=bare).exists())

    def test_plans_are_for_platform_admins_only(self):
        user = get_user_model().objects.create_user(username="staff", password="StrongPass123")
        api = APIClient()
        api.force_authenticate(user)
        self.assertEqual(api.get(PLANS).status_code, 403)
        self.assertEqual(api.post(PLANS, {"nomi": "X1"}, format="json").status_code, 403)
