"""Register the server's polling bot (TELEGRAM_BOT_TOKEN) as one library's bot.

    python manage.py link_polling_bot asosiy-kutubxona
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import ValidationError

from organization.models import Organization
from telegrambot.services import link_polling_bot


class Command(BaseCommand):
    help = "Link the .env polling bot to an organization (no webhook is set)."

    def add_arguments(self, parser):
        parser.add_argument("slug")

    def handle(self, *args, **options):
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        if not token:
            raise CommandError("TELEGRAM_BOT_TOKEN is not set.")
        try:
            org = Organization.objects.get(slug=options["slug"])
        except Organization.DoesNotExist:
            raise CommandError(f"Organization {options['slug']!r} not found.")
        try:
            bot = link_polling_bot(org, token)
        except ValidationError as error:
            raise CommandError(str(error.detail))
        self.stdout.write(f"Linked @{bot.username} to {org.slug} (polling, status {bot.holati}).")
