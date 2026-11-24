from celery import shared_task

from .health import beat


@shared_task
def heartbeat():
    """Runs every minute from beat. A fresh timestamp proves beat and a worker are alive."""
    beat("celery")
    return "ok"


@shared_task
def check_bots():
    """Re-verify every connected Telegram bot (token valid, webhook set)."""
    from telegrambot.models import TelegramBot
    from telegrambot.services import botni_tekshirish

    n = 0
    for bot in TelegramBot.objects.exclude(holati="uzilgan"):
        botni_tekshirish(bot)
        n += 1
    beat("bot_check", checked=n)
    return n
