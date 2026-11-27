from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from organization.models import Membership, Organization, OrganizationSubscription, SubscriptionPlan
from organization.services import subscription_for

from . import taps
from .models import Payment, PaymentPart
from .services import add_months, price, split_amount, sync_pending

User = get_user_model()
CREATED = {"donationId": "d-1", "checkoutUrl": "https://pay.example/1", "totalAmount": 60000, "commissionAmount": 1800}


class BillingBase(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(nomi="Lib", slug="lib", status=Organization.HOLAT_ACTIVE)
        self.owner = User.objects.create_user(username="owner", password="StrongPass123")
        Membership.objects.create(organization=self.org, user=self.owner, rol="egasi")
        self.plan = SubscriptionPlan.objects.get(code="standard")
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def checkout(self, months=3, method="click"):
        with mock.patch("billing.taps.create_donation", return_value=CREATED) as create:
            response = self.client.post("/api/billing/checkout/", {"months": months, "method": method}, format="json")
        return response, create


class PriceTest(BillingBase):
    def test_standard_plan_seeded_at_60k(self):
        self.assertEqual(int(self.plan.narx_oylik), 60000)
        self.assertEqual([price(self.plan, m) for m in (1, 3, 6, 12)], [60000, 180000, 360000, 720000])

    @override_settings(BILLING_DISCOUNTS={12: 15})
    def test_discount(self):
        self.assertEqual(price(self.plan, 12), 612000)

    def test_split_amount_respects_taps_cap(self):
        self.assertEqual(split_amount(180000, 200000), [180000])
        self.assertEqual(split_amount(360000, 200000), [180000, 180000])
        self.assertEqual(split_amount(720000, 200000), [180000] * 4)
        self.assertEqual(split_amount(612000, 200000), [153000] * 4)
        self.assertEqual(split_amount(250000, 200000), [125000, 125000])

    def test_add_months_clamps_day(self):
        moment = timezone.now().replace(year=2026, month=1, day=31)
        self.assertEqual(add_months(moment, 1).day, 28)
        self.assertEqual(add_months(moment, 12).year, 2027)


class CheckoutTest(BillingBase):
    def test_overview_lists_periods_and_methods(self):
        data = self.client.get("/api/billing/").data
        self.assertEqual(data["plans"][0]["code"], "standard")
        self.assertEqual([p["months"] for p in data["plans"][0]["periods"]], [1, 3, 6, 12])
        self.assertIn("payme", [m["code"] for m in data["methods"]])

    def test_checkout_then_paid_extends_subscription(self):
        sub = subscription_for(self.org)
        trial_end = sub.trial_ends_at
        response, create = self.checkout(months=3)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["checkout_url"], CREATED["checkoutUrl"])
        self.assertEqual(create.call_args.kwargs["amount"], 180000)

        payment_id = response.data["id"]
        with mock.patch("billing.taps.donation_status", return_value={"status": "Created"}):
            self.assertEqual(self.client.get(f"/api/billing/payments/{payment_id}/").data["status"], "pending")
        paid = {"status": "Paid", "paidTime": "2026-11-27T10:00:00", "amount": 180000, "donateAmount": 174600}
        with mock.patch("billing.taps.donation_status", return_value=paid):
            data = self.client.get(f"/api/billing/payments/{payment_id}/").data
            # A second check must not add the months twice.
            self.client.get(f"/api/billing/payments/{payment_id}/")
        self.assertEqual(data["status"], "paid")
        sub.refresh_from_db()
        self.assertEqual(sub.status, "active")
        self.assertEqual(sub.plan, self.plan)
        # Remaining trial days are kept: the 3 months start at the trial end.
        self.assertEqual(sub.current_period_end, add_months(trial_end, 3))

    def test_underpaid_is_not_applied(self):
        response, _ = self.checkout(months=1)
        with mock.patch("billing.taps.donation_status", return_value={"status": "Paid", "amount": 1000}):
            self.client.get(f"/api/billing/payments/{response.data['id']}/")
        self.assertEqual(Payment.objects.get().status, "pending")

    def test_dead_and_stale_payments_are_cancelled(self):
        response, _ = self.checkout()
        with mock.patch("billing.taps.donation_status", return_value={"status": "Cancelled"}):
            sync_pending()
        self.assertEqual(Payment.objects.get().status, "cancelled")

        self.checkout()
        PaymentPart.objects.filter(payment__status="pending").update(created_at=timezone.now() - timedelta(hours=3))
        with mock.patch("billing.taps.donation_status", return_value={"status": "Created"}):
            sync_pending()
        self.assertFalse(Payment.objects.filter(status="pending").exists())

    def test_provider_failure_returns_502(self):
        with mock.patch("billing.taps.create_donation", side_effect=taps.TapsError("down")):
            response = self.client.post("/api/billing/checkout/", {"months": 1, "method": "click"}, format="json")
        self.assertEqual(response.status_code, 502)
        self.assertEqual(Payment.objects.get().status, "cancelled")

    def test_bad_input_and_roles(self):
        self.assertEqual(self.checkout(months=2)[0].status_code, 400)
        self.assertEqual(self.checkout(method="card")[0].status_code, 400)
        Membership.objects.filter(user=self.owner).update(rol="kutubxonachi")
        self.assertEqual(self.checkout()[0].status_code, 403)
        self.assertEqual(self.client.get("/api/billing/").status_code, 403)

    def test_other_library_payment_hidden(self):
        other = Organization.objects.create(nomi="Other", slug="other", status=Organization.HOLAT_ACTIVE)
        payment = Payment.objects.create(organization=other, plan=self.plan, months=1, amount=60000, method="click")
        self.assertEqual(self.client.get(f"/api/billing/payments/{payment.pk}/").status_code, 404)


class EnforcementTest(BillingBase):
    def expire(self):
        sub = subscription_for(self.org)
        OrganizationSubscription.objects.filter(pk=sub.pk).update(
            status="trial", trial_ends_at=timezone.now() - timedelta(days=1)
        )

    def test_off_by_default(self):
        self.expire()
        response = self.client.post("/api/books/", {}, format="json")
        self.assertNotEqual(response.status_code, 403)

    @override_settings(BILLING_ENFORCE=True)
    def test_expired_library_reads_but_cannot_write(self):
        self.expire()
        self.assertEqual(self.client.get("/api/books/").status_code, 200)
        response = self.client.post("/api/books/", {}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"], "subscription_expired")
        # Paying is still possible.
        self.assertEqual(self.checkout()[0].status_code, 201)

    @override_settings(BILLING_ENFORCE=True)
    def test_active_library_writes(self):
        response = self.client.post("/api/books/", {}, format="json")
        self.assertNotEqual(response.status_code, 403)


class SplitPaymentTest(BillingBase):
    def test_year_is_paid_in_four_parts(self):
        donations = iter(range(1, 20))

        def create(**kwargs):
            n = next(donations)
            return {"donationId": f"d-{n}", "checkoutUrl": f"https://pay.example/{n}"}

        with mock.patch("billing.taps.create_donation", side_effect=create) as created:
            response = self.client.post("/api/billing/checkout/", {"months": 12, "method": "payme"}, format="json")
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual((response.data["parts_total"], response.data["part_amount"]), (4, 180000))
            self.assertEqual(created.call_count, 1)  # later parts are opened one by one
            paid = set()

            def status(donation_id):
                return {"status": "Paid", "amount": 180000} if donation_id in paid else {"status": "Draft"}

            with mock.patch("billing.taps.donation_status", side_effect=status):
                url = f"/api/billing/payments/{response.data['id']}/"
                for n in range(1, 5):
                    data = self.client.get(url).data
                    self.assertEqual(data["status"], "pending")
                    self.assertEqual(data["parts_paid"], n - 1)
                    self.assertEqual(data["checkout_url"], f"https://pay.example/{n}")
                    paid.add(f"d-{n}")
                data = self.client.get(url).data
        self.assertEqual(data["status"], "paid")
        self.assertEqual(data["parts_paid"], 4)
        sub = subscription_for(self.org)
        self.assertGreater(sub.current_period_end, timezone.now() + timedelta(days=360))

    def test_half_paid_payment_is_never_cancelled(self):
        donations = iter(range(1, 20))
        create = lambda **kw: {"donationId": f"d-{next(donations)}", "checkoutUrl": "https://pay.example/x"}  # noqa: E731
        with mock.patch("billing.taps.create_donation", side_effect=create):
            response = self.client.post("/api/billing/checkout/", {"months": 6, "method": "click"}, format="json")
            status = lambda donation_id: {"status": "Paid", "amount": 180000} if donation_id == "d-1" else {"status": "Draft"}  # noqa: E731
            with mock.patch("billing.taps.donation_status", side_effect=status):
                sync_pending()  # part 1 paid, part 2 opened as d-2
                PaymentPart.objects.filter(index=2).update(created_at=timezone.now() - timedelta(hours=3))
                sync_pending()
                self.assertEqual(Payment.objects.get().status, "pending")
                # The page asks for a fresh link; the old one is still watched.
                self.client.get(f"/api/billing/payments/{response.data['id']}/")
                part = PaymentPart.objects.get(index=2)
                self.assertEqual(part.provider_payment_id, "d-3")
                self.assertEqual(part.meta["previous_ids"], ["d-2"])
            late = lambda donation_id: {"status": "Paid", "amount": 180000} if donation_id in ("d-1", "d-2") else {"status": "Draft"}  # noqa: E731
            with mock.patch("billing.taps.donation_status", side_effect=late):
                sync_pending()
        self.assertEqual(Payment.objects.get().status, "paid")
