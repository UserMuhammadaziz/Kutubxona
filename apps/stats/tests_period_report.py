"""Period statistics, Excel export, reminders and the daily Telegram report."""

from datetime import date, time, timedelta
from io import BytesIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from berish.models import Berish
from kitob.models import Kitob
from organization.models import Membership, Organization
from oquvchi.models import Oquvchi
from stats import tasks
from stats.models import ReminderLog
from stats.report import build_period_report, local_today, resolve_period

User = get_user_model()


class ResolvePeriodTest(TestCase):
    def test_presets(self):
        today = date(2026, 11, 27)  # Friday
        self.assertEqual(resolve_period("today", today=today), (today, today))
        self.assertEqual(resolve_period("yesterday", today=today), (date(2026, 11, 26),) * 2)
        self.assertEqual(resolve_period("tomorrow", today=today), (date(2026, 11, 28),) * 2)
        self.assertEqual(resolve_period("week", today=today), (date(2026, 11, 23), date(2026, 11, 29)))
        self.assertEqual(resolve_period("month", today=today), (date(2026, 11, 1), date(2026, 11, 30)))
        self.assertEqual(
            resolve_period("custom", "2026-01-01", "2026-01-31", today=today),
            (date(2026, 1, 1), date(2026, 1, 31)),
        )

    def test_bad_custom_range(self):
        with self.assertRaises(ValueError):
            resolve_period("custom", "2026-02-01", "2026-01-01")
        with self.assertRaises(ValueError):
            resolve_period("custom", "bad", "2026-01-01")
        with self.assertRaises(ValueError):
            resolve_period("custom", "2024-01-01", "2026-01-01")


class PeriodReportBase(TestCase):
    def setUp(self):
        self.today = local_today()
        self.org = Organization.objects.create(nomi="Hisobot kutubxonasi", status=Organization.HOLAT_ACTIVE)
        self.user = User.objects.create_user(username="lib", password="parol12345", full_name="Kutubxonachi Ali")
        self.membership = Membership.objects.create(organization=self.org, user=self.user, rol="kutubxonachi")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.book = Kitob.objects.create(
            organization=self.org, nomi="O'tkan kunlar", muallif="Qodiriy", janr="badiiy", nashr_yili=2020
        )
        self.readers = [
            Oquvchi.objects.create(
                organization=self.org,
                fish=f"O'quvchi {i}",
                telefon=f"+99890123456{i}",
                karta_raqami=f"K{i}",
                sinf="7-A",
                telegram_id=1000 + i if i % 2 == 0 else None,
            )
            for i in range(4)
        ]

    def loan(self, reader, due, returned=None, issued=None):
        return Berish.objects.create(
            organization=self.org,
            kitob=self.book,
            oquvchi=reader,
            bergan_xodim=self.user,
            berilgan_sana=issued or due - timedelta(days=14),
            qaytarish_muddati=due,
            qaytarilgan_sana=returned,
            olgan_xodim=self.user if returned else None,
        )


class PeriodReportTest(PeriodReportBase):
    def test_due_today_split_into_returned_and_not_returned(self):
        on_time = self.loan(self.readers[0], self.today, returned=self.today)
        missing = self.loan(self.readers[1], self.today)
        self.loan(self.readers[2], self.today + timedelta(days=1))  # due tomorrow: not in today's list
        overdue = self.loan(self.readers[3], self.today - timedelta(days=3))

        report = build_period_report(self.org, self.today, self.today, today=self.today)
        summary = report["summary"]
        self.assertEqual(summary["due"], 2)
        self.assertEqual(summary["returned_on_time"], 1)
        self.assertEqual(summary["not_returned"], 1)
        self.assertEqual([r["id"] for r in report["not_returned"]], [missing.pk])
        self.assertEqual({r["id"] for r in report["overdue"]}, {overdue.pk})
        self.assertEqual(report["overdue"][0]["late_days"], 3)
        self.assertEqual(summary["returned"], 1)
        self.assertEqual(report["returned"][0]["id"], on_time.pk)
        self.assertEqual(report["by_staff"], [{"name": "Kutubxonachi Ali", "issued": 0, "received": 1}])

    def test_api_tomorrow_and_isolation(self):
        tomorrow = self.loan(self.readers[2], self.today + timedelta(days=1))
        other_org = Organization.objects.create(nomi="Boshqa", status=Organization.HOLAT_ACTIVE)
        other_reader = Oquvchi.objects.create(
            organization=other_org, fish="Begona", telefon="+998909999999", karta_raqami="X1"
        )
        other_book = Kitob.objects.create(
            organization=other_org, nomi="Begona kitob", muallif="A", janr="badiiy", nashr_yili=2020
        )
        Berish.objects.create(
            organization=other_org, kitob=other_book, oquvchi=other_reader,
            qaytarish_muddati=self.today + timedelta(days=1),
        )

        response = self.client.get("/api/stats/period/", {"preset": "tomorrow"})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual([r["id"] for r in response.data["due"]], [tomorrow.pk])
        self.assertEqual(response.data["due"][0]["telegram_linked"], True)

    def test_api_rejects_bad_period(self):
        response = self.client.get("/api/stats/period/", {"preset": "custom", "start": "x", "end": "y"})
        self.assertEqual(response.status_code, 400)

    def test_requires_staff(self):
        stranger = User.objects.create_user(username="stranger", password="parol12345")
        client = APIClient()
        client.force_authenticate(stranger)
        self.assertEqual(client.get("/api/stats/period/").status_code, 403)

    def test_excel_export(self):
        from openpyxl import load_workbook

        self.loan(self.readers[1], self.today)
        response = self.client.get("/api/stats/period/export/", {"preset": "today"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])
        workbook = load_workbook(BytesIO(response.content))
        self.assertIn("Qaytarmaganlar", workbook.sheetnames)
        rows = list(workbook["Qaytarmaganlar"].iter_rows(values_only=True))
        self.assertEqual(rows[1][0], "O'quvchi 1")


class ReminderTest(PeriodReportBase):
    def test_manual_reminder_logged_and_cooled_down(self):
        loan = self.loan(self.readers[0], self.today - timedelta(days=2))
        with mock.patch("stats.reminders.telegram_xabar_yubor", return_value=True) as send:
            first = self.client.post("/api/stats/remind/", {"loan_id": loan.pk}, format="json")
            second = self.client.post("/api/stats/remind/", {"loan_id": loan.pk}, format="json")
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(send.call_count, 1)
        log = ReminderLog.objects.get()
        self.assertEqual((log.kind, log.delivered, log.sent_by), (ReminderLog.KIND_MANUAL, True, self.user))

        report = build_period_report(self.org, self.today, self.today, today=self.today)
        self.assertTrue(report["overdue"][0]["reminder"]["delivered"])
        self.assertEqual(report["summary"]["reminders_sent"], 1)

    def test_manual_reminder_needs_telegram(self):
        loan = self.loan(self.readers[1], self.today)
        response = self.client.post("/api/stats/remind/", {"loan_id": loan.pk}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_overdue_task_repeats_only_after_pause(self):
        self.loan(self.readers[0], self.today - timedelta(days=5))
        self.loan(self.readers[1], self.today - timedelta(days=5))  # no Telegram
        with mock.patch("stats.reminders.telegram_xabar_yubor", return_value=True) as send:
            tasks.send_overdue_reminders()
            tasks.send_overdue_reminders()
        self.assertEqual(send.call_count, 1)
        self.assertEqual(ReminderLog.objects.filter(kind=ReminderLog.KIND_OVERDUE).count(), 1)


class DailyReportTaskTest(PeriodReportBase):
    def setUp(self):
        super().setUp()
        self.membership.telegram_id = 555
        self.membership.save()
        owner = User.objects.create_user(username="owner", password="parol12345")
        Membership.objects.create(organization=self.org, user=owner, rol="egasi", telegram_id=556)

    def run_at(self, hour, minute=0):
        from django.utils import timezone

        from stats.report import local_tz

        moment = timezone.now().astimezone(local_tz()).replace(hour=hour, minute=minute)
        with mock.patch("stats.tasks.timezone.now", return_value=moment), mock.patch(
            "config.telegram.send_telegram_document", return_value=True
        ) as send:
            tasks.send_daily_reports()
        return send

    def test_sent_once_after_report_time_to_all_staff(self):
        self.org.daily_report_time = time(18, 0)
        self.org.save()
        self.assertEqual(self.run_at(17, 55).call_count, 0)
        send = self.run_at(18, 0)
        self.assertEqual({c.args[0] for c in send.call_args_list}, {555, 556})
        filename, content = send.call_args.args[1], send.call_args.args[2]
        self.assertTrue(filename.endswith(".xlsx"))
        self.assertTrue(content.startswith(b"PK"))
        self.assertEqual(self.run_at(18, 5).call_count, 0)  # already sent today

    def test_librarians_only_and_disabled(self):
        self.org.daily_report_recipients = Organization.REPORT_RECIPIENTS_LIBRARIANS
        self.org.daily_report_time = time(9, 0)
        self.org.save()
        send = self.run_at(9, 1)
        self.assertEqual([c.args[0] for c in send.call_args_list], [555])

        Organization.objects.filter(pk=self.org.pk).update(daily_report_enabled=False, daily_report_last_sent=None)
        self.assertEqual(self.run_at(9, 2).call_count, 0)

    def test_settings_editable_via_api(self):
        self.membership.rol = "egasi"
        self.membership.save()
        response = self.client.patch(
            f"/api/organizations/{self.org.pk}/",
            {"daily_report_time": "17:30", "daily_report_recipients": "librarians", "daily_report_enabled": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.org.refresh_from_db()
        self.assertEqual(self.org.daily_report_time, time(17, 30))
        self.assertEqual(self.org.daily_report_recipients, "librarians")
