"""Applications must never end up without a library.

An account without a membership could save an application with an empty
organization, which no librarian can see.
"""
from importlib import import_module
from unittest.mock import patch

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from config.telegram import telegram_xabar_yubor
from oquvchi.models import Ariza, Oquvchi
from oquvchi.services import arizani_tasdiqla
from organization.models import Membership, Organization
from telegrambot.client import TelegramAPIError

User = get_user_model()
ACTIVE = Organization.HOLAT_ACTIVE
URL = "/api/applications/"


class ApplicationLibraryTest(TestCase):
    def setUp(self):
        # Data migrations may leave a default library behind.
        Organization.objects.all().delete()
        self.org = self.make_org("main")
        self.bot = self.client_for(User.objects.create_user(username="svc", password="parol12345"))

    def make_org(self, slug, status=ACTIVE):
        return Organization.objects.create(nomi=slug, slug=f"app-{slug}", status=status)

    def client_for(self, user):
        api = APIClient()
        api.force_authenticate(user)
        return api

    def payload(self, telegram_id=900):
        return {
            "telegram_id": telegram_id, "fish": "Alisher Karimov",
            "telefon": "+998901234567", "rol": "oqituvchi", "kasb": "Matematika",
        }

    def make_application(self, telegram_id=900, org=None, **extra):
        data = {**self.payload(telegram_id), **extra}
        return Ariza.objects.create(organization=org, **data)

    def make_reader(self, org, telegram_id, phone="+998907777777", **extra):
        return Oquvchi.objects.create(
            organization=org, rol="oqituvchi", fish="T T", telefon=phone,
            telegram_id=telegram_id, **extra,
        )

    # --- API ---
    def test_service_account_application_joins_the_only_library(self):
        res = self.bot.post(URL, self.payload(), format="json")
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(Ariza.objects.get().organization, self.org)

    def test_service_account_sees_status_and_cannot_duplicate(self):
        self.bot.post(URL, self.payload(), format="json")
        res = self.bot.get(f"{URL}status/", {"telegram_id": 900})
        self.assertEqual(res.data["holati"], "kutmoqda")
        self.assertEqual(self.bot.post(URL, self.payload(), format="json").status_code, 400)
        self.assertEqual(Ariza.objects.count(), 1)

    def test_rejected_when_library_is_ambiguous(self):
        self.make_org("second")
        for api in (self.bot, APIClient()):
            res = api.post(URL, self.payload(), format="json")
            self.assertEqual(res.status_code, 400, res.data)
        self.assertEqual(Ariza.objects.count(), 0)

    def test_member_of_an_inactive_library_is_not_moved_to_another(self):
        pending = self.make_org("pending", Organization.HOLAT_PENDING)
        user = User.objects.create_user(username="p", password="parol12345")
        Membership.objects.create(organization=pending, user=user, rol="egasi")
        res = self.client_for(user).post(URL, self.payload(), format="json")
        self.assertEqual(res.status_code, 400, res.data)
        self.assertEqual(Ariza.objects.count(), 0)

    def test_disabled_member_gets_no_library(self):
        user = User.objects.create_user(username="d", password="parol12345")
        Membership.objects.create(
            organization=self.org, user=user, rol="kutubxonachi", faol=False
        )
        res = self.client_for(user).post(URL, self.payload(), format="json")
        self.assertEqual(res.status_code, 400, res.data)

    # --- approval ---
    def test_approval_links_the_application(self):
        application = self.make_application()
        _, reader, _ = arizani_tasdiqla(application, organization=self.org)
        application.refresh_from_db()
        self.assertEqual(reader.organization, self.org)
        self.assertEqual(application.organization, self.org)

    def test_approval_survives_an_existing_linked_application(self):
        self.make_application(org=self.org, holati="bekor")
        application = self.make_application()
        arizani_tasdiqla(application, organization=self.org)
        application.refresh_from_db()
        self.assertEqual(application.holati, "tasdiqlandi")
        self.assertIsNone(application.organization)

    # --- migration ---
    def migrate(self):
        import_module("oquvchi.migrations.0015_link_orphan_applications").link(
            django_apps, None
        )

    def test_migration_links_to_the_only_active_library(self):
        self.make_org("old", Organization.HOLAT_ARCHIVED)
        application, reader = self.make_application(), self.make_reader(None, 901)
        self.migrate()
        application.refresh_from_db(), reader.refresh_from_db()
        self.assertEqual(application.organization, self.org)
        self.assertEqual(reader.organization, self.org)

    def test_migration_prefers_the_readers_library(self):
        second = self.make_org("second")
        self.make_reader(second, 900)
        known, unknown = self.make_application(900), self.make_application(902)
        self.migrate()
        known.refresh_from_db(), unknown.refresh_from_db()
        self.assertEqual(known.organization, second)
        self.assertIsNone(unknown.organization)

    def test_migration_keeps_duplicates_and_links_the_pending_one(self):
        pending = self.make_application()
        rejected = self.make_application(holati="bekor")
        self.migrate()
        pending.refresh_from_db(), rejected.refresh_from_db()
        self.assertEqual(pending.organization, self.org)
        self.assertIsNone(rejected.organization)

    def test_migration_leaves_a_reader_whose_phone_is_taken(self):
        self.make_reader(self.org, 910)
        orphan = self.make_reader(None, 911)
        self.migrate()
        orphan.refresh_from_db()
        self.assertIsNone(orphan.organization)
        self.assertEqual(orphan.telefon, "+998907777777")

    # --- delivery ---
    def deliver(self, status):
        tokens = []

        def send(token, *args, **kwargs):
            tokens.append(token)
            if token == "org-token":
                raise TelegramAPIError("sendMessage", "error", status)

        with (
            override_settings(TELEGRAM_BOT_TOKEN="global-token"),
            patch("config.telegram._token_ol", return_value="org-token"),
            patch("telegrambot.client.send_message", side_effect=send),
        ):
            return telegram_xabar_yubor(900, "x", organization=self.org), tokens

    def test_rejected_message_falls_back_to_the_global_bot(self):
        self.assertEqual(self.deliver(403), (True, ["org-token", "global-token"]))

    def test_no_second_send_after_a_timeout(self):
        self.assertEqual(self.deliver(None), (False, ["org-token"]))

    def test_no_global_fallback_with_several_libraries(self):
        self.make_org("second")
        self.assertEqual(self.deliver(403), (False, ["org-token"]))
