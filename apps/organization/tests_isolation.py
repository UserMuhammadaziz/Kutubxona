"""Cross-tenant regressions: foreign FKs on copies, shared staff, ISBN, fines, reminders."""
from datetime import timedelta
from importlib import import_module
from unittest.mock import patch

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from berish.models import Berish
from berish.services import kitob_ber
from jarima.models import Jarima
from jarima.tasks import jarima_eslatma_yubor
from kitob.models import Kitob
from navbat.models import Navbat
from nusxa.models import Nusxa
from nusxa.serializers import NusxaYaratishSerializer
from oquvchi.models import Oquvchi
from organization.models import Membership, Organization

User = get_user_model()


class IsolationBase(TestCase):
    def setUp(self):
        self.org_a, self.org_b = (
            Organization.objects.create(nomi=n, slug=f"iso-{n}", status=Organization.HOLAT_ACTIVE)
            for n in ("a", "b")
        )
        self.owner_a = self.make_user("owner_a", self.org_a, "egasi")
        self.admin_a = self.make_user("admin_a", self.org_a, "administrator")
        self.staff_a = self.make_user("staff_a", self.org_a, "kutubxonachi")
        self.book_a = self.make_book(self.org_a, "A book")
        self.book_b = self.make_book(self.org_b, "B book", isbn="ISBN-B")
        self.api = self.login(self.admin_a)

    def make_user(self, username, org, role):
        user = User.objects.create_user(
            username=username, password="parol12345", full_name=username, rol="administrator"
        )
        Membership.objects.create(organization=org, user=user, rol=role)
        return user

    def make_book(self, org, title, **extra):
        return Kitob.objects.create(
            organization=org, nomi=title, muallif="M", janr="badiiy", nashr_yili=2020, **extra
        )

    def make_reader(self, org, n):
        return Oquvchi.objects.create(
            organization=org, rol="oquvchi", fish=f"R{n}", telefon=f"+99890200000{n}",
            sinf="7-A", telegram_id=500 + n,
        )

    def make_copy(self, org, book, number):
        return Nusxa.objects.create(
            organization=org, kitob=book, inventar_raqami=number, holati="mavjud",
            qabul_sana=timezone.localdate(),
        )

    def make_loan(self, org, book, reader):
        today = timezone.localdate()
        return Berish.objects.create(
            organization=org, kitob=book, oquvchi=reader,
            berilgan_sana=today - timedelta(days=20),
            qaytarish_muddati=today - timedelta(days=3),
        )

    def login(self, user, org=None):
        client = APIClient()
        client.force_authenticate(User.objects.get(pk=user.pk))
        client.credentials(HTTP_X_ORGANIZATION_ID=str((org or self.org_a).pk))
        return client


class CopyForeignBookTest(IsolationBase):
    def post(self, book, number):
        return self.api.post(
            "/api/copies/", {"kitob": book.pk, "inventar_raqami": number}, format="json"
        )

    def test_create_rejects_foreign_book(self):
        res = self.post(self.book_b, "X-1")
        self.assertEqual(res.status_code, 400, res.data)
        self.assertFalse(Nusxa.objects.filter(kitob=self.book_b).exists())
        self.assertEqual(self.post(self.book_a, "X-2").status_code, 201)

    def test_patch_rejects_foreign_book(self):
        copy = self.make_copy(self.org_a, self.book_a, "X-3")
        res = self.api.patch(f"/api/copies/{copy.pk}/", {"kitob": self.book_b.pk}, format="json")
        self.assertEqual(res.status_code, 400, res.data)
        copy.refresh_from_db()
        self.assertEqual(copy.kitob_id, self.book_a.pk)

    def test_missing_organization_fails_closed(self):
        serializer = NusxaYaratishSerializer(data={"kitob": self.book_b.pk, "inventar_raqami": "X"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("kitob", serializer.errors)

    def test_loan_rejects_foreign_copy_of_own_book(self):
        copy = self.make_copy(self.org_a, self.book_b, "X-4")
        with self.assertRaises(Exception) as ctx:
            kitob_ber(copy, self.make_reader(self.org_b, 1), self.admin_a)
        self.assertIn("boshqa kutubxona", str(ctx.exception))
        copy.refresh_from_db()
        self.assertEqual(copy.holati, "mavjud")


class IsbnScopeTest(IsolationBase):
    def post(self):
        return self.api.post(
            "/api/books/",
            {"nomi": "N", "muallif": "M", "janr": "badiiy", "til": "", "nashr_yili": 2020, "isbn": "ISBN-B"},
            format="json",
        )

    def test_same_isbn_allowed_across_libraries_only(self):
        res = self.post()
        self.assertEqual(res.status_code, 201, res.data)
        again = self.post()
        self.assertEqual(again.status_code, 400)
        self.assertIn("isbn", str(again.data))


class StaffIsolationTest(IsolationBase):
    def patch(self, user, data, client=None):
        return (client or self.api).patch(f"/api/staff/{user.pk}/", data, format="json")

    def share(self, role="egasi"):
        return Membership.objects.create(organization=self.org_b, user=self.staff_a, rol=role)

    def membership(self, user, org=None):
        return Membership.objects.get(user=user, organization=org or self.org_a)

    def test_block_affects_this_library_only(self):
        self.share()
        res = self.patch(self.staff_a, {"is_active": False})
        self.assertEqual(res.status_code, 200, res.data)
        self.assertFalse(res.data["is_active"])
        self.staff_a.refresh_from_db()
        self.assertTrue(self.staff_a.is_active)
        self.assertFalse(self.membership(self.staff_a).faol)
        self.assertTrue(self.membership(self.staff_a, self.org_b).faol)
        self.assertEqual(self.login(self.staff_a).get("/api/books/").status_code, 403)
        self.assertEqual(self.login(self.staff_a, self.org_b).get("/api/books/").status_code, 200)

    def test_blocked_staff_stays_listed_and_can_be_reactivated(self):
        self.patch(self.staff_a, {"is_active": False})
        rows = {r["id"]: r for r in self.api.get("/api/staff/").data["results"]}
        self.assertFalse(rows[self.staff_a.pk]["is_active"])
        res = self.patch(self.staff_a, {"is_active": True})
        self.assertEqual(res.status_code, 200, res.data)
        self.assertTrue(res.data["is_active"])
        self.assertEqual(self.login(self.staff_a).get("/api/books/").status_code, 200)

    def test_reactivates_account_blocked_by_the_old_global_flag(self):
        User.objects.filter(pk=self.staff_a.pk).update(is_active=False)
        self.assertEqual(self.patch(self.staff_a, {"is_active": True}).status_code, 200)
        self.staff_a.refresh_from_db()
        self.assertTrue(self.staff_a.is_active)

    def test_globally_blocked_shared_account_cannot_be_reactivated(self):
        self.share()
        User.objects.filter(pk=self.staff_a.pk).update(is_active=False)
        self.assertEqual(self.patch(self.staff_a, {"is_active": True}).status_code, 400)

    def test_reactivation_respects_staff_limit(self):
        self.patch(self.staff_a, {"is_active": False})
        with patch("organization.services.plan_limit", return_value=2):
            res = self.patch(self.staff_a, {"is_active": True})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(self.membership(self.staff_a).faol)

    def test_shared_account_personal_data_is_locked(self):
        self.share()
        for field in ("username", "full_name", "telefon"):
            self.assertEqual(self.patch(self.staff_a, {field: "hijacked"}).status_code, 400, field)
        self.staff_a.refresh_from_db()
        self.assertEqual(self.staff_a.username, "staff_a")

    def test_unchanged_personal_data_is_accepted_for_shared_account(self):
        self.share()
        res = self.patch(self.staff_a, {"username": "staff_a", "rol": "administrator"})
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(self.membership(self.staff_a).rol, "administrator")
        self.assertEqual(self.membership(self.staff_a, self.org_b).rol, "egasi")

    def test_sole_member_personal_data_is_editable(self):
        res = self.patch(self.staff_a, {"full_name": "New name", "rol": "kutubxonachi"})
        self.assertEqual(res.status_code, 200, res.data)
        self.staff_a.refresh_from_db()
        self.assertEqual((self.staff_a.full_name, self.staff_a.rol), ("New name", "kutubxonachi"))

    def test_platform_account_personal_data_is_locked(self):
        User.objects.filter(pk=self.staff_a.pk).update(is_staff=True)
        self.assertEqual(self.patch(self.staff_a, {"username": "hijacked"}).status_code, 400)

    def test_admin_cannot_touch_owner(self):
        for data in ({"rol": "kutubxonachi"}, {"is_active": False}, {"username": "hijacked"}):
            self.assertEqual(self.patch(self.owner_a, data).status_code, 403, data)
        self.owner_a.refresh_from_db()
        self.assertTrue(self.owner_a.is_active)
        self.assertEqual(self.membership(self.owner_a).rol, "egasi")

    def test_owner_edits_own_name_but_not_role(self):
        client = self.login(self.owner_a)
        self.assertEqual(self.patch(self.owner_a, {"full_name": "Boss"}, client).status_code, 200)
        self.assertEqual(self.patch(self.owner_a, {"rol": "kutubxonachi"}, client).status_code, 400)
        self.assertEqual(self.patch(self.owner_a, {"is_active": False}, client).status_code, 400)
        self.assertEqual(self.membership(self.owner_a).rol, "egasi")

    def test_list_hides_other_memberships(self):
        self.share()
        rows = {r["id"]: r for r in self.api.get("/api/staff/").data["results"]}
        row = rows[self.staff_a.pk]
        self.assertEqual([k["id"] for k in row["kutubxonalar"]], [self.org_a.pk])
        self.assertEqual(row["joriy_rol"], "kutubxonachi")
        self.assertEqual(row["rol"], "kutubxonachi")

    def test_foreign_staff_is_not_found(self):
        other = self.make_user("only_b", self.org_b, "egasi")
        self.assertEqual(self.patch(other, {"is_active": False}).status_code, 404)


class FineIsolationTest(IsolationBase):
    def test_fines_cannot_be_created_through_api(self):
        loan = self.make_loan(self.org_b, self.book_b, self.make_reader(self.org_b, 1))
        for pk in (loan.pk, 999999):
            res = self.api.post("/api/fines/", {"berish": pk}, format="json")
            self.assertEqual(res.status_code, 405)

    def test_reminder_uses_readers_library_bot(self):
        loan = self.make_loan(self.org_b, self.book_b, self.make_reader(self.org_b, 1))
        Jarima.objects.create(organization=self.org_b, berish=loan, kechikkan_kunlar=3, summa=100)
        with patch("jarima.tasks.telegram_xabar_yubor", return_value=True) as send:
            jarima_eslatma_yubor()
        self.assertEqual(send.call_args.kwargs.get("organization"), self.org_b)


class RepairMisassignedRowsTest(IsolationBase):
    def repair(self):
        module = import_module("organization.migrations.0011_repair_misassigned_rows")
        module.repair(django_apps, None)

    def test_moves_row_only_when_parents_agree(self):
        reader_b = self.make_reader(self.org_b, 1)
        reader_a = self.make_reader(self.org_a, 2)
        wrong = Navbat.objects.create(organization=self.org_a, kitob=self.book_b, oquvchi=reader_b)
        ambiguous = Navbat.objects.create(organization=self.org_a, kitob=self.book_b, oquvchi=reader_a)
        correct = Navbat.objects.create(organization=self.org_a, kitob=self.book_a, oquvchi=reader_a)
        loan = self.make_loan(self.org_a, self.book_b, reader_b)
        fine = Jarima.objects.create(organization=self.org_a, berish=loan, kechikkan_kunlar=1, summa=1)
        self.repair()
        for row, org in (
            (wrong, self.org_b), (ambiguous, self.org_a), (correct, self.org_a),
            (loan, self.org_b), (fine, self.org_b),
        ):
            row.refresh_from_db()
            self.assertEqual(row.organization_id, org.pk, row)
