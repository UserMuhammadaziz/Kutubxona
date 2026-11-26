from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from organization.models import Organization

from .attribution import normalise
from .models import SignupAttribution, Visit

User = get_user_model()
VISITOR = "a1b2c3d4-0000-4000-8000-123456789abc"


class NormaliseTest(TestCase):
    def test_utm_tags_win(self):
        data = normalise({"utm_source": "Google", "utm_medium": "CPC", "utm_campaign": "kuz-2026", "referrer": "https://t.me/x"})
        self.assertEqual((data["source"], data["medium"], data["campaign"]), ("google", "cpc", "kuz-2026"))
        self.assertEqual(data["referrer_host"], "t.me")

    def test_referrer_and_click_ids(self):
        self.assertEqual(normalise({"referrer": "https://www.google.co.uz/"})["source"], "google")
        self.assertEqual(normalise({"referrer": "https://www.google.co.uz/"})["medium"], "organic")
        self.assertEqual(normalise({"referrer": "https://t.me/kanal"})["source"], "telegram")
        self.assertEqual(normalise({"referrer": "https://l.instagram.com/"})["source"], "instagram")
        self.assertEqual((normalise({"gclid": "x"})["source"], normalise({"gclid": "x"})["medium"]), ("google", "cpc"))
        self.assertEqual(normalise({"referrer": "https://blog.uz/post"})["medium"], "referral")
        self.assertEqual(normalise({})["source"], "direct")

    def test_own_host_is_not_a_referrer(self):
        self.assertEqual(normalise({"referrer": "https://kutubxona.uz/welcome"}, "kutubxona.uz")["source"], "direct")

    def test_garbage_is_trimmed(self):
        data = normalise({"utm_campaign": "x" * 500, "path": "javascript:alert(1)", "visitor_id": "<script>"})
        self.assertEqual(len(data["campaign"]), 120)
        self.assertEqual((data["landing_path"], data["visitor_id"]), ("", ""))


class VisitAndSignupTest(TestCase):
    def setUp(self):
        cache.clear()

    def visit(self, **extra):
        return APIClient().post("/api/marketing/visit/", {"visitor_id": VISITOR, "path": "/welcome", **extra}, format="json")

    def test_visit_recorded_once_per_session(self):
        self.assertEqual(self.visit(utm_source="google", utm_medium="cpc").status_code, 204)
        self.visit(utm_source="google", utm_medium="cpc")
        self.visit(utm_source="telegram")
        self.assertEqual(Visit.objects.count(), 2)

    def test_visit_needs_visitor_id(self):
        self.assertEqual(APIClient().post("/api/marketing/visit/", {}, format="json").status_code, 400)

    def register(self, **extra):
        return APIClient().post(
            "/api/auth/register/",
            {
                "kutubxona_nomi": "Yangi kutubxona",
                "full_name": "Ali Valiyev",
                "telefon": "+998901112233",
                "password": "Parol12345!",
                "password_confirm": "Parol12345!",
                **extra,
            },
            format="json",
        )

    def test_signup_stores_first_and_last_touch(self):
        self.visit(utm_source="google", utm_medium="cpc", utm_campaign="kuz")
        res = self.register(attribution={
            "first": {"visitor_id": VISITOR, "utm_source": "google", "utm_medium": "cpc", "utm_campaign": "kuz"},
            "last": {"visitor_id": VISITOR, "referrer": "https://t.me/kanal"},
        })
        self.assertEqual(res.status_code, 201, res.data)
        a = SignupAttribution.objects.get()
        self.assertEqual((a.source, a.medium, a.campaign, a.last_source), ("google", "cpc", "kuz", "telegram"))
        self.assertIsNotNone(a.first_seen_at)

    def test_signup_without_attribution_still_works(self):
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(SignupAttribution.objects.get().source, "direct")

    def test_broken_attribution_never_blocks_signup(self):
        self.assertEqual(self.register(attribution="nonsense").status_code, 201)
        self.assertEqual(self.register(telefon="+998901112244", attribution={"first": [1, 2]}).status_code, 201)


class ReportTest(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_user(username="root", password="x", is_staff=True)

    def test_report_groups_sources_and_counts_conversion(self):
        for i in range(4):
            Visit.objects.create(visitor_id=f"visitor-{i:04d}", source="google", medium="cpc", campaign="kuz")
        Visit.objects.create(visitor_id="visitor-9999", source="direct", medium="none")
        org = Organization.objects.create(nomi="A", slug="a", status=Organization.HOLAT_ACTIVE)
        SignupAttribution.objects.create(organization=org, source="google", medium="cpc", campaign="kuz")
        Organization.objects.create(nomi="B", slug="b")  # registered before tracking

        api = APIClient()
        api.force_authenticate(self.admin)
        data = api.get("/api/marketing/report/?days=7").json()

        self.assertEqual(data["totals"]["visitors"], 5)
        google = next(r for r in data["sources"] if r["source"] == "google")
        self.assertEqual((google["visitors"], google["signups"], google["approved"], google["conversion"]), (4, 1, 1, 25.0))
        self.assertTrue(any(r["source"] == "unknown" for r in data["sources"]))
        self.assertEqual(data["campaigns"][0]["campaign"], "kuz")
        self.assertEqual(data["recent_signups"][0]["organization_name"], "A")

    def test_report_is_platform_only(self):
        api = APIClient()
        api.force_authenticate(User.objects.create_user(username="lib", password="x"))
        self.assertEqual(api.get("/api/marketing/report/").status_code, 403)
        self.assertEqual(APIClient().get("/api/marketing/report/").status_code, 401)
