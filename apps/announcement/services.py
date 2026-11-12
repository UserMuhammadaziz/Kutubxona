from datetime import date

from django.db.models import Exists, OuterRef
from django.utils import timezone

from berish.models import Berish
from config.telegram import telegram_escape
from jarima.models import Jarima
from oquvchi.models import Oquvchi
from telegrambot.services import botni_ol, xabar_yubor

from .models import Announcement

DAILY_LIMIT = 3  # announcements per organization per day
MAX_RECIPIENTS = 500


def audience_queryset(organization, audience, grade=""):
    """Active readers of the organization reachable via Telegram."""
    qs = Oquvchi.objects.filter(
        organization=organization, faol=True, telegram_id__isnull=False
    )
    if audience == "students":
        qs = qs.filter(rol="oquvchi")
    elif audience == "teachers":
        qs = qs.filter(rol="oqituvchi")
    elif audience == "overdue":
        qs = qs.filter(
            Exists(
                Berish.objects.filter(
                    oquvchi=OuterRef("pk"),
                    qaytarilgan_sana__isnull=True,
                    qaytarish_muddati__lt=date.today(),
                )
            )
        )
    elif audience == "debtors":
        qs = qs.filter(
            Exists(Jarima.objects.filter(berish__oquvchi=OuterRef("pk"), tolandimi=False))
        )
    if grade:
        qs = qs.filter(sinf=grade)
    return qs


def sent_today(organization):
    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return Announcement.objects.filter(organization=organization, created_at__gte=start).count()


def send_announcement(organization, user, text, audience, grade=""):
    """Send synchronously; returns the saved Announcement with counters."""
    bot = botni_ol(organization)
    readers = list(audience_queryset(organization, audience, grade)[:MAX_RECIPIENTS])
    sent = failed = 0
    body = telegram_escape(text)
    for reader in readers:
        if xabar_yubor(bot, reader.telegram_id, body):
            sent += 1
        else:
            failed += 1
    return Announcement.objects.create(
        organization=organization,
        text=text,
        audience=audience,
        grade=grade,
        created_by=user,
        recipients_count=len(readers),
        sent_count=sent,
        failed_count=failed,
    )
