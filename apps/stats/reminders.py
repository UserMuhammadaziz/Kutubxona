"""Overdue-loan reminders: message text, sending and history."""

from datetime import timedelta

from django.utils import timezone

from config.telegram import telegram_escape, telegram_xabar_yubor

from .models import ReminderLog
from .report import local_today

# How often an overdue reader is reminded again by the scheduled task.
OVERDUE_REPEAT_DAYS = 3
# A manual reminder is refused if one was delivered this recently.
MANUAL_COOLDOWN = timedelta(minutes=10)


def overdue_text(loan, today=None):
    today = today or local_today()
    days = (today - loan.qaytarish_muddati).days
    inventory = f"Inventar raqami: {loan.nusxa.inventar_raqami}\n" if loan.nusxa_id else ""
    if days > 0:
        head = "🔴 <b>Kitobni qaytarish muddati o'tdi!</b>"
        tail = f"Muddat <b>{days} kun</b> oldin tugagan — jarima yozilishi mumkin."
    elif days == 0:
        head = "⏰ <b>Bugun kitobni qaytarish kuni!</b>"
        tail = "Iltimos, bugun kutubxonaga olib keling."
    else:
        head = "⏰ <b>Kitobni qaytarish muddati yaqinlashmoqda</b>"
        tail = f"Qolgan kun: <b>{-days}</b>"
    return (
        f"{head}\n\n"
        f"📖 <b>{telegram_escape(loan.kitob.nomi)}</b>\n"
        f"{inventory}"
        f"Qaytarish muddati: <b>{loan.qaytarish_muddati}</b>\n"
        f"{tail}\n\n"
        "Iltimos, kitobni kutubxonaga qaytaring!"
    )


def log_reminder(loan, kind, delivered, sent_by=None):
    return ReminderLog.objects.create(
        organization_id=loan.organization_id,
        loan=loan,
        kind=kind,
        delivered=delivered,
        sent_by=sent_by,
    )


def send_loan_reminder(loan, kind, sent_by=None, today=None):
    """Send one reminder and record it. Returns True when Telegram accepted it."""
    chat_id = loan.oquvchi.telegram_id
    if not chat_id:
        return False
    try:
        delivered = telegram_xabar_yubor(chat_id, overdue_text(loan, today), organization=loan.organization)
    except Exception:
        delivered = False
    log_reminder(loan, kind, bool(delivered), sent_by=sent_by)
    return bool(delivered)


def recently_reminded(loan, since):
    return ReminderLog.objects.filter(loan=loan, delivered=True, sent_at__gte=since).exists()


def manual_cooldown_active(loan):
    return recently_reminded(loan, timezone.now() - MANUAL_COOLDOWN)
