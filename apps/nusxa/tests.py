"""Adding several copies at once and the per-status counts on the copies page."""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from kitob.models import Kitob
from nusxa.models import Nusxa
from nusxa.serializers import inventory_numbers
from organization.models import Membership, Organization

User = get_user_model()


class InventoryNumbersTest(TestCase):
    def test_keeps_prefix_and_padding(self):
        self.assertEqual(inventory_numbers("INV-008", 3), ["INV-008", "INV-009", "INV-010"])
        self.assertEqual(inventory_numbers("99", 2), ["99", "100"])

    def test_single_copy_needs_no_digits(self):
        self.assertEqual(inventory_numbers("A", 1), ["A"])


class CopiesApiTest(TestCase):
    def setUp(self):
        cache.clear()
        self.org = Organization.objects.create(nomi="Maktab", slug="maktab", status=Organization.HOLAT_ACTIVE)
        other = Organization.objects.create(nomi="Boshqa", slug="other", status=Organization.HOLAT_ACTIVE)
        user = User.objects.create_user(username="lib", password="parol12345")
        Membership.objects.create(organization=self.org, user=user, rol="kutubxonachi", faol=True)
        self.api = APIClient()
        self.api.force_authenticate(user)
        self.book = Kitob.objects.create(organization=self.org, nomi="Alpomish", muallif="Xalq", janr="badiiy", nashr_yili=2020)
        other_book = Kitob.objects.create(organization=other, nomi="X", muallif="Y", janr="badiiy", nashr_yili=2020)
        Nusxa.objects.create(organization=other, kitob=other_book, inventar_raqami="INV-001", qabul_sana="2026-01-01")

    def post(self, **data):
        return self.api.post("/api/copies/", {"kitob": self.book.pk, "inventar_raqami": "INV-001", **data}, format="json")

    def test_bulk_create(self):
        res = self.post(count=3)
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["created_count"], 3)
        self.assertEqual(
            sorted(Nusxa.objects.filter(organization=self.org).values_list("inventar_raqami", flat=True)),
            ["INV-001", "INV-002", "INV-003"],
        )

    def test_duplicate_inside_range_creates_nothing(self):
        Nusxa.objects.create(organization=self.org, kitob=self.book, inventar_raqami="INV-002", qabul_sana="2026-01-01")
        res = self.post(count=3)
        self.assertEqual(res.status_code, 400)
        self.assertIn("INV-002", str(res.data))
        self.assertEqual(Nusxa.objects.filter(organization=self.org).count(), 1)

    def test_count_limits_and_digits(self):
        self.assertEqual(self.post(count=0).status_code, 400)
        self.assertEqual(self.post(count=201).status_code, 400)
        self.assertEqual(self.post(inventar_raqami="ABC", count=2).status_code, 400)

    def test_summary_is_per_tenant_and_follows_search(self):
        self.post(count=3)
        Nusxa.objects.filter(inventar_raqami="INV-003", organization=self.org).update(holati="berilgan")
        data = self.api.get("/api/copies/summary/").json()
        self.assertEqual(data["total"], 3)
        self.assertEqual(data["by_status"], {"mavjud": 2, "berilgan": 1})
        self.assertEqual(self.api.get("/api/copies/summary/", {"search": "INV-003"}).json()["total"], 1)

    def test_book_list_search(self):
        Kitob.objects.create(organization=self.org, nomi="Boshqa kitob", muallif="Z", janr="badiiy", nashr_yili=2020)
        data = self.api.get("/api/books/", {"search": "alpom"}).json()
        self.assertEqual([b["nomi"] for b in data["results"]], ["Alpomish"])
