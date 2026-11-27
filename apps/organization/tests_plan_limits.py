"""Plan limits for books and readers are enforced, not only shown."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from config.test_helpers import TenantTestMixin
from kitob.models import Kitob
from oquvchi.models import Oquvchi
from oquvchi.services import oquvchi_yarat
from organization.models import SubscriptionPlan
from organization.services import subscription_for

User = get_user_model()


class PlanLimitTest(TenantTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        plan = SubscriptionPlan.objects.create(
            code="tiny", nomi="Tiny", narx_oylik=0, max_staff=5, max_resources=2, max_customers=2
        )
        sub = subscription_for(self.org)
        sub.plan = plan
        sub.save(update_fields=["plan"])
        self.user = User.objects.create_user(username="lib", password="parol12345", rol="kutubxonachi")
        self.azolik(self.user)
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def add_book(self, n):
        return self.api.post(
            "/api/books/",
            {"nomi": f"Kitob {n}", "muallif": "Muallif", "janr": "badiiy", "nashr_yili": 2020},
            format="json",
        )

    def test_book_over_limit_is_rejected(self):
        self.assertEqual(self.add_book(1).status_code, 201)
        self.assertEqual(self.add_book(2).status_code, 201)
        res = self.add_book(3)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["error"], "obuna_limiti")
        self.assertEqual(Kitob.objects.filter(organization=self.org).count(), 2)

    def test_reader_over_limit_is_rejected(self):
        for i in range(2):
            oquvchi_yarat(organization=self.org, fish=f"R{i}", telefon=f"+99890000000{i}")
        with self.assertRaises(ValidationError):
            oquvchi_yarat(organization=self.org, fish="R3", telefon="+998900000009")
        self.assertEqual(Oquvchi.objects.filter(organization=self.org).count(), 2)

    def test_unlimited_plan_allows_more(self):
        sub = subscription_for(self.org)
        sub.plan.max_resources = None
        sub.plan.save(update_fields=["max_resources"])
        for n in range(4):
            self.assertEqual(self.add_book(n).status_code, 201)
