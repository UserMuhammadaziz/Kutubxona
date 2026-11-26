"""Sweep of every tenant endpoint: library A must never see or touch library B's rows."""
import json

from announcement.models import Announcement
from jarima.models import Jarima
from kitob.models import BandQilish
from navbat.models import Navbat
from oquvchi.models import Ariza
from organization.models import AuditLog, Membership, Organization, PushSubscription

from .tests_isolation import IsolationBase

LIST_ENDPOINTS = [
    "/api/books/",
    "/api/copies/",
    "/api/readers/",
    "/api/applications/",
    "/api/loans/",
    "/api/fines/",
    "/api/reservations/",
    "/api/holds/",
    "/api/announcements/",
    "/api/staff/",
    "/api/organizations/",
]


class TenantSweepTest(IsolationBase):
    def setUp(self):
        super().setUp()
        self.secret = "SECRET-B-7731"
        self.org_b.nomi = self.secret
        self.org_b.save()
        self.owner_b = self.make_user("owner_b_secret", self.org_b, "egasi")
        self.reader_b = self.make_reader(self.org_b, 7)
        self.reader_b.fish = self.secret
        self.reader_b.sinf = "11-Z"
        self.reader_b.save()
        self.copy_b = self.make_copy(self.org_b, self.book_b, "INV-SECRET")
        self.loan_b = self.make_loan(self.org_b, self.book_b, self.reader_b)
        self.fine_b = Jarima.objects.create(organization=self.org_b, berish=self.loan_b, kechikkan_kunlar=3, summa=15000)
        self.res_b = Navbat.objects.create(organization=self.org_b, kitob=self.book_b, oquvchi=self.reader_b)
        self.hold_b = BandQilish.objects.create(organization=self.org_b, kitob=self.book_b, oquvchi=self.reader_b)
        self.app_b = Ariza.objects.create(organization=self.org_b, telegram_id=999, fish=self.secret, telefon="+998909999999", sinf="11-Z")
        self.ann_b = Announcement.objects.create(organization=self.org_b, text=self.secret, audience="all")
        self.membership_b = Membership.objects.get(user=self.owner_b)
        # Library A has data too, so empty answers can't pass by accident.
        self.reader_a = self.make_reader(self.org_a, 1)
        self.copy_a = self.make_copy(self.org_a, self.book_a, "INV-A")
        self.make_loan(self.org_a, self.book_a, self.reader_a)
        self.owner_api = self.login(self.owner_a)

    def body(self, res):
        return json.dumps(res.json() if res.content else {}, ensure_ascii=False, default=str)

    def assert_clean(self, res, url):
        self.assertNotIn(self.secret, self.body(res), url)
        self.assertNotIn("INV-SECRET", self.body(res), url)
        self.assertNotIn("11-Z", self.body(res), url)

    def test_lists_never_show_foreign_rows(self):
        for api in (self.api, self.owner_api):
            for url in LIST_ENDPOINTS:
                res = api.get(url)
                self.assertIn(res.status_code, (200, 403), f"{url}: {res.status_code}")
                self.assert_clean(res, url)

    def test_list_filters_cannot_reach_foreign_rows(self):
        for url in (
            f"/api/copies/?kitob={self.book_b.pk}",
            f"/api/loans/?oquvchi={self.reader_b.pk}",
            f"/api/reservations/?kitob={self.book_b.pk}",
            f"/api/books/?search={self.secret}",
            f"/api/readers/?search={self.secret}",
            f"/api/readers/?sinf=11-Z",
            f"/api/fines/?berish={self.loan_b.pk}",
        ):
            self.assert_clean(self.owner_api.get(url), url)

    def test_foreign_detail_is_not_found(self):
        details = {
            "books": self.book_b,
            "copies": self.copy_b,
            "readers": self.reader_b,
            "applications": self.app_b,
            "loans": self.loan_b,
            "fines": self.fine_b,
            "reservations": self.res_b,
            "announcements": self.ann_b,
            "staff": self.owner_b,
        }
        for name, obj in details.items():
            url = f"/api/{name}/{obj.pk}/"
            res = self.owner_api.get(url)
            self.assertIn(res.status_code, (403, 404, 405), f"GET {url}: {res.status_code}")
            self.assert_clean(res, url)
            for method in ("patch", "put", "delete"):
                res = getattr(self.owner_api, method)(url, {}, format="json")
                self.assertIn(res.status_code, (400, 403, 404, 405), f"{method} {url}: {res.status_code}")
        # Nothing of B changed.
        for obj in details.values():
            self.assertTrue(type(obj).objects.filter(pk=obj.pk).exists(), obj)

    def test_foreign_organization_is_hidden(self):
        url = f"/api/organizations/{self.org_b.pk}/"
        self.assertIn(self.owner_api.get(url).status_code, (403, 404))
        self.assertIn(self.owner_api.patch(url, {"nomi": "hack"}, format="json").status_code, (403, 404))
        self.org_b.refresh_from_db()
        self.assertEqual(self.org_b.nomi, self.secret)

    def test_spoofed_organization_header_is_refused(self):
        spoof = self.login(self.owner_a, org=self.org_b)
        for url in LIST_ENDPOINTS[:-1] + ["/api/stats/dashboard/", "/api/auth/organization/", "/api/messages/classes/"]:
            res = spoof.get(url)
            self.assertIn(res.status_code, (400, 403, 404), f"{url}: {res.status_code}")
            self.assert_clean(res, url)

    def test_stats_and_messages_are_scoped(self):
        for url in (
            "/api/stats/dashboard/",
            "/api/stats/top-books/",
            "/api/stats/recent-activity/",
            "/api/stats/ratings/me/",
            "/api/messages/classes/",
            "/api/auth/organization/",
            "/api/auth/memberships/",
            "/api/auth/me/",
            "/api/telegram/settings/",
            "/api/stats/ratings/",
            "/api/stats/ratings/overall/",
            "/api/stats/ratings/activity/",
            "/api/stats/ratings/competition/",
            "/api/issue-reports/",
            "/api/auth/xatolik-xabari/",
        ):
            res = self.owner_api.get(url)
            self.assertIn(res.status_code, (200, 403, 404, 405), f"{url}: {res.status_code}")
            self.assert_clean(res, url)

    def test_unknown_api_path_is_json_404(self):
        res = self.owner_api.get(f"/api/holds/{self.hold_b.pk}/")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(self.owner_api.get("/api/no-such-endpoint/").status_code, 404)

    def test_writes_with_foreign_references_are_rejected(self):
        attempts = [
            ("/api/loans/", {"nusxa": self.copy_b.pk, "oquvchi": self.reader_a.pk}),
            ("/api/loans/", {"nusxa": self.copy_a.pk, "oquvchi": self.reader_b.pk}),
            ("/api/reservations/", {"kitob": self.book_b.pk, "oquvchi": self.reader_a.pk}),
            ("/api/reservations/", {"kitob": self.book_a.pk, "oquvchi": self.reader_b.pk}),
            ("/api/holds/", {"kitob": self.book_b.pk, "oquvchi": self.reader_a.pk}),
            ("/api/holds/", {"kitob": self.book_a.pk, "nusxa": self.copy_b.pk, "oquvchi": self.reader_a.pk}),
            ("/api/books/", {"nomi": "X", "muallif": "M", "janr": "badiiy", "nashr_yili": 2020, "organization": self.org_b.pk}),
        ]
        before = {m: m.objects.filter(organization=self.org_b).count() for m in (Navbat, BandQilish)}
        for url, payload in attempts:
            res = self.owner_api.post(url, payload, format="json")
            if res.status_code in (200, 201):
                # Accepted only when it stayed inside library A.
                self.assertEqual(res.json().get("organization", self.org_a.pk), self.org_a.pk, f"{url} {payload}")
                self.assertNotEqual(url, "/api/loans/", payload)
                self.assertNotIn(url, ("/api/reservations/", "/api/holds/"), payload)
            else:
                self.assertIn(res.status_code, (400, 403, 404), f"{url} {payload}: {res.status_code}")
        self.copy_b.refresh_from_db()
        self.assertEqual(self.copy_b.holati, "mavjud")
        for model, count in before.items():
            self.assertEqual(model.objects.filter(organization=self.org_b).count(), count, model)
        from kitob.models import Kitob

        self.assertEqual(Kitob.objects.filter(organization=self.org_b).count(), 1)

    def test_foreign_application_cannot_be_decided(self):
        for action in ("approve", "reject", "tasdiqlash", "rad_etish"):
            res = self.owner_api.post(f"/api/applications/{self.app_b.pk}/{action}/", {}, format="json")
            self.assertIn(res.status_code, (403, 404, 405), f"{action}: {res.status_code}")
        self.app_b.refresh_from_db()
        self.assertEqual(self.app_b.holati, "kutmoqda")

    def test_foreign_loan_cannot_be_returned_or_extended(self):
        for action in ("return", "qaytarish", "extend", "uzaytirish", "renew"):
            res = self.owner_api.post(f"/api/loans/{self.loan_b.pk}/{action}/", {}, format="json")
            self.assertIn(res.status_code, (403, 404, 405), f"{action}: {res.status_code}")
        self.loan_b.refresh_from_db()
        self.assertIsNone(self.loan_b.qaytarilgan_sana)

    def test_platform_data_is_closed_to_tenants(self):
        AuditLog.objects.create(organization=self.org_b, action="x", metadata={"nomi": self.secret})
        PushSubscription.objects.create(user=self.owner_b, organization=self.org_b, endpoint="https://p/1", p256dh="k", auth="a")
        for url in (
            "/api/saas/organizations/",
            "/api/saas/organizations/stats/",
            f"/api/saas/organizations/{self.org_b.pk}/details/",
            "/api/saas/audit/",
            "/api/saas/plans/",
            "/api/saas/health/",
            "/api/marketing/report/",
        ):
            res = self.owner_api.get(url)
            self.assertEqual(res.status_code, 403, f"{url}: {res.status_code}")
            self.assert_clean(res, url)
