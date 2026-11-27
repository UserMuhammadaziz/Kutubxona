"""Organization type (library / school) and the configurable dashboard."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from organization.dashboard import available_widgets
from organization.models import Membership, Organization
from oquvchi.models import Ariza, Oquvchi
from telegrambot import handler
from telegrambot.models import TelegramBot

User = get_user_model()


class OrgTestBase(TestCase):
    org_type = Organization.TYPE_LIBRARY

    def setUp(self):
        cache.clear()
        Organization.objects.all().delete()
        self.org = Organization.objects.create(
            nomi="Shahar kutubxonasi", slug="city", type=self.org_type, status=Organization.HOLAT_ACTIVE
        )

    def member(self, role, username):
        user = User.objects.create_user(username=username, password="parol12345")
        Membership.objects.create(organization=self.org, user=user, rol=role, faol=True)
        api = APIClient()
        api.force_authenticate(user)
        return api


class OrganizationTypeApiTest(OrgTestBase):
    def test_type_is_exposed_in_english(self):
        data = self.member("egasi", "owner").get("/api/auth/organization/").json()
        self.assertEqual(data["type"], "library")
        self.assertNotIn("turi", data)

    def platform_admin(self):
        user = User.objects.create_user(username="root", password="parol12345", is_staff=True)
        api = APIClient()
        api.force_authenticate(user)
        return api

    def test_owner_type_change_waits_for_platform_approval(self):
        owner = self.member("egasi", "owner")
        res = owner.patch(f"/api/organizations/{self.org.pk}/", {"type": "school"}, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual((res.data["type"], res.data["requested_type"]), ("library", "school"))
        self.org.refresh_from_db()
        self.assertEqual(self.org.type, "library")
        self.assertIsNotNone(self.org.type_requested_at)

        admin = self.platform_admin()
        listed = {o["id"]: o for o in admin.get("/api/saas/organizations/stats/").json()["tashkilotlar"]}
        self.assertEqual(listed[self.org.pk]["requested_type"], "school")
        res = admin.post(f"/api/saas/organizations/{self.org.pk}/type-request/approve/")
        self.assertEqual(res.status_code, 200, res.data)
        self.org.refresh_from_db()
        self.assertEqual((self.org.type, self.org.requested_type), ("school", ""))
        self.assertEqual(admin.post(f"/api/saas/organizations/{self.org.pk}/type-request/approve/").status_code, 409)

    def test_platform_rejects_type_request(self):
        self.member("egasi", "owner").patch(f"/api/organizations/{self.org.pk}/", {"type": "school"}, format="json")
        res = self.platform_admin().post(f"/api/saas/organizations/{self.org.pk}/type-request/reject/")
        self.assertEqual(res.status_code, 200, res.data)
        self.org.refresh_from_db()
        self.assertEqual((self.org.type, self.org.requested_type), ("library", ""))

    def test_owner_withdraws_request_by_choosing_current_type(self):
        owner = self.member("egasi", "owner")
        owner.patch(f"/api/organizations/{self.org.pk}/", {"type": "school"}, format="json")
        res = owner.patch(f"/api/organizations/{self.org.pk}/", {"type": "library"}, format="json")
        self.assertEqual(res.data["requested_type"], "")

    def test_platform_admin_sets_type_directly(self):
        self.member("egasi", "owner").patch(f"/api/organizations/{self.org.pk}/", {"type": "school"}, format="json")
        res = self.platform_admin().patch(f"/api/saas/organizations/{self.org.pk}/", {"type": "school"}, format="json")
        self.assertEqual(res.status_code, 200, res.data)
        self.org.refresh_from_db()
        self.assertEqual((self.org.type, self.org.requested_type), ("school", ""))

    def test_owner_cannot_approve_own_request(self):
        owner = self.member("egasi", "owner")
        owner.patch(f"/api/organizations/{self.org.pk}/", {"type": "school"}, format="json")
        self.assertEqual(owner.post(f"/api/saas/organizations/{self.org.pk}/type-request/approve/").status_code, 403)

    def test_administrator_cannot_switch_type(self):
        res = self.member("administrator", "admin").patch(
            f"/api/organizations/{self.org.pk}/", {"type": "school"}, format="json"
        )
        self.assertEqual(res.status_code, 400)
        self.org.refresh_from_db()
        self.assertEqual(self.org.type, "library")

    def test_unknown_type_rejected(self):
        res = self.member("egasi", "owner").patch(
            f"/api/organizations/{self.org.pk}/", {"type": "office"}, format="json"
        )
        self.assertEqual(res.status_code, 400)

    def test_register_with_type(self):
        res = APIClient().post(
            "/api/auth/register/",
            {
                "kutubxona_nomi": "Yangi maktab",
                "type": "school",
                "full_name": "Ali Valiyev",
                "telefon": "+998901112233",
                "password": "Parol12345!",
                "password_confirm": "Parol12345!",
            },
            format="json",
        )
        self.assertIn(res.status_code, (200, 201), res.data)
        self.assertEqual(Organization.objects.get(nomi="Yangi maktab").type, "school")


class DashboardWidgetsTest(OrgTestBase):
    def test_default_widgets_follow_type(self):
        data = self.member("egasi", "owner").get("/api/auth/organization/").json()
        self.assertEqual(data["dashboard_widgets"], available_widgets("library"))
        self.assertIn("members_count", data["available_dashboard_widgets"])
        self.assertNotIn("teachers_count", data["available_dashboard_widgets"])

    def test_admin_saves_order_and_dashboard_uses_it(self):
        api = self.member("administrator", "admin")
        res = api.patch(
            f"/api/organizations/{self.org.pk}/",
            {"dashboard_widgets": ["top_books", "overdue_loans"]},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.json()["dashboard_widgets"], ["top_books", "overdue_loans"])
        stats = self.member("kutubxonachi", "lib").get("/api/stats/dashboard/").json()
        self.assertEqual(stats["widgets"], ["top_books", "overdue_loans"])

    def test_widget_change_is_not_hidden_by_stats_cache(self):
        lib = self.member("kutubxonachi", "lib")
        lib.get("/api/stats/dashboard/")
        self.org.dashboard_widgets = ["total_books"]
        self.org.save()
        self.assertEqual(lib.get("/api/stats/dashboard/").json()["widgets"], ["total_books"])

    def test_widgets_of_other_type_are_hidden_not_lost(self):
        self.org.dashboard_widgets = ["teachers_count", "total_books"]
        self.org.save()
        api = self.member("egasi", "owner")
        self.assertEqual(api.get("/api/stats/dashboard/").json()["widgets"], ["total_books"])
        self.org.type = Organization.TYPE_SCHOOL
        self.org.save()
        self.assertEqual(
            api.get("/api/stats/dashboard/").json()["widgets"], ["teachers_count", "total_books"]
        )

    def test_invalid_widget_lists_rejected(self):
        api = self.member("egasi", "owner")
        for bad in (["nope"], ["top_books", "top_books"], "top_books", [1]):
            res = api.patch(
                f"/api/organizations/{self.org.pk}/", {"dashboard_widgets": bad}, format="json"
            )
            self.assertEqual(res.status_code, 400, bad)

    def test_librarian_cannot_change_widgets(self):
        res = self.member("kutubxonachi", "lib").patch(
            f"/api/organizations/{self.org.pk}/", {"dashboard_widgets": []}, format="json"
        )
        self.assertEqual(res.status_code, 403)

    def test_members_count(self):
        Oquvchi.objects.create(organization=self.org, fish="A B", telefon="+998900000001", karta_raqami="1")
        stats = self.member("egasi", "owner").get("/api/stats/dashboard/").json()
        self.assertEqual(stats["members_count"], 1)


class LibraryReaderFieldsTest(OrgTestBase):
    def reader_payload(self, **extra):
        return {"fish": "Ali Valiyev", "telefon": "+998901234567", **extra}

    def test_library_reader_requires_address_and_birth_date(self):
        res = self.member("kutubxonachi", "lib").post("/api/readers/", self.reader_payload(), format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("manzil", str(res.data))

    def test_library_reader_created_without_class(self):
        res = self.member("kutubxonachi", "lib").post(
            "/api/readers/",
            self.reader_payload(manzil="Toshkent, Chilonzor", tugilgan_sana="2001-03-15", sinf="7-A", rol="oqituvchi"),
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)
        reader = Oquvchi.objects.get()
        self.assertEqual((reader.rol, reader.sinf, reader.manzil), ("oquvchi", "", "Toshkent, Chilonzor"))

    def test_library_application_needs_address_and_birth_date(self):
        bot = self.member("kutubxonachi", "svc")
        base = {"telegram_id": 77, "fish": "Ali Valiyev", "telefon": "+998901234567"}
        self.assertEqual(bot.post("/api/applications/", base, format="json").status_code, 400)
        res = bot.post(
            "/api/applications/",
            {**base, "manzil": "Toshkent", "tugilgan_sana": "2001-03-15"},
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)
        self.assertIsNone(Ariza.objects.get().sinf)

    def test_future_birth_date_rejected(self):
        res = self.member("kutubxonachi", "lib").post(
            "/api/readers/",
            self.reader_payload(manzil="Toshkent", tugilgan_sana="2999-01-01"),
            format="json",
        )
        self.assertEqual(res.status_code, 400)


class SchoolReaderFieldsTest(OrgTestBase):
    org_type = Organization.TYPE_SCHOOL

    def test_school_reader_still_needs_class(self):
        bot = self.member("kutubxonachi", "svc")
        res = bot.post(
            "/api/applications/",
            {"telegram_id": 78, "fish": "Ali Valiyev", "telefon": "+998901234567", "rol": "oquvchi"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("sinf", str(res.data))


class LibraryBotFlowTest(OrgTestBase):
    def setUp(self):
        super().setUp()
        self.bot = TelegramBot.objects.create(
            organization=self.org,
            telegram_bot_id=4242,
            token_encrypted="x",
            webhook_path="city-hook",
            webhook_secret="s",
            holati="ulangan",
        )
        self.sent = []
        patcher = patch.object(handler, "_send", side_effect=lambda b, c, text, markup=None: self.sent.append((text, markup)))
        patcher.start()
        self.addCleanup(patcher.stop)
        patch.object(handler, "answer_callback_query").start()
        self.addCleanup(patch.stopall)

    def text(self, value):
        handler.handle_update(self.bot, {"message": {"chat": {"id": 5}, "from": {"id": 5}, "text": value}})

    def test_join_button_then_address_and_birth_date(self):
        self.text("/start")
        buttons = self.sent[-1][1]["inline_keyboard"]
        self.assertEqual([b["callback_data"] for row in buttons for b in row], ["rol:oquvchi"])

        handler.handle_update(
            self.bot,
            {"callback_query": {"id": "c", "from": {"id": 5}, "message": {"chat": {"id": 5}, "message_id": 1}, "data": "rol:oquvchi"}},
        )
        self.text("Ali Valiyev")
        self.text("+998901234567")
        self.assertEqual(self.sent[-1][0], handler.QUESTION_ADDRESS)
        self.text("Toshkent, Chilonzor 5")
        self.assertEqual(self.sent[-1][0], handler.QUESTION_BIRTH_DATE)
        self.text("31.02.2001")  # not a real date: asked again
        self.assertIn("Sana noto'g'ri", self.sent[-1][0])
        self.text("15.03.2001")

        ariza = Ariza.objects.get()
        self.assertEqual(ariza.manzil, "Toshkent, Chilonzor 5")
        self.assertEqual(str(ariza.tugilgan_sana), "2001-03-15")
        self.assertEqual((ariza.rol, ariza.sinf), ("oquvchi", None))

    def test_teacher_role_ignored_in_library(self):
        handler.handle_update(
            self.bot,
            {"callback_query": {"id": "c", "from": {"id": 6}, "message": {"chat": {"id": 6}, "message_id": 1}, "data": "rol:oqituvchi"}},
        )
        self.assertFalse(self.bot.sessiyalar.exists())


class SchoolDashboardCountsTest(OrgTestBase):
    org_type = Organization.TYPE_SCHOOL

    def test_application_counts_and_class_breakdown(self):
        for i, raw in enumerate(["7a", "7-A sinf", '9-"B"', "7 д", ""]):
            Oquvchi.objects.create(organization=self.org, fish=f"O {i}", telefon=f"+99890000010{i}", karta_raqami=f"S{i}", sinf=raw)
        Oquvchi.objects.create(organization=self.org, rol="oqituvchi", fish="T", telefon="+998900000200", karta_raqami="T1")
        for i, status in enumerate(["kutmoqda", "kutmoqda", "tasdiqlandi", "bekor"]):
            Ariza.objects.create(organization=self.org, telegram_id=100 + i, fish="A B", telefon="+998900000300", holati=status, sinf="7-A")

        stats = self.member("egasi", "owner").get("/api/stats/dashboard/").json()

        self.assertEqual((stats["pending_applications"], stats["approved_applications"]), (2, 1))
        self.assertEqual(
            stats["readers_by_class"],
            [
                {"class_name": "7-A", "count": 2},
                {"class_name": "7-D", "count": 1},
                {"class_name": "9-B", "count": 1},
                {"class_name": "", "count": 1},
            ],
        )
        self.assertEqual((stats["members_count"], stats["oqituvchi_soni"]), (6, 1))
        self.assertIn("readers_by_class", stats["widgets"])

    def test_new_application_is_not_hidden_by_stats_cache(self):
        api = self.member("egasi", "owner")
        api.get("/api/stats/dashboard/")
        Ariza.objects.create(organization=self.org, telegram_id=1, fish="A B", telefon="+998900000300", sinf="5-A")
        self.assertEqual(api.get("/api/stats/dashboard/").json()["pending_applications"], 1)

    def test_class_breakdown_is_school_only(self):
        self.assertNotIn("readers_by_class", available_widgets(Organization.TYPE_LIBRARY))
