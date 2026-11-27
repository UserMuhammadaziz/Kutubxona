import os
from celery import Celery
from celery.schedules import crontab
from celery.signals import after_setup_logger, after_setup_task_logger

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("kutubxona")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@after_setup_logger.connect
@after_setup_task_logger.connect
def _error_alerts(logger, **kwargs):
    """Celery replaces the root handlers, so the Telegram alert handler is added back here."""
    from config.error_alerts import attach

    attach(logger, process_name="celery")

app.conf.beat_schedule = {
    "heartbeat-har-daqiqada": {
        "task": "organization.tasks.heartbeat",
        "schedule": crontab(minute="*"),
    },
    "botlarni-har-10-daqiqada-tekshir": {
        "task": "organization.tasks.check_bots",
        "schedule": crontab(minute="*/10"),
    },
    "jarimalarni-har-kuni-hisobla": {
        "task": "jarima.tasks.jarimalarni_hisobla",
        "schedule": crontab(hour=0, minute=30),
    },
    "jarima-eslatmalar-har-3-soatda": {
        "task": "jarima.tasks.jarima_eslatma_yubor",
        "schedule": crontab(minute=0, hour="*/3"),
    },
    "takliflarni-har-10-daqiqada-tekshir": {
        "task": "navbat.tasks.takliflarni_tekshir",
        "schedule": crontab(minute="*/10"),
    },
    "ochiq-navbatlarni-har-10-daqiqada-tekshir": {
        "task": "navbat.tasks.ochiq_navbatlarni_tekshir",
        "schedule": crontab(minute="*/10"),
    },
    "eslatmalarni-har-kuni-yubor": {
        "task": "berish.tasks.eslatma_yuborish",
        "schedule": crontab(hour=9, minute=0),
    },
    # Har oyning 1-kuni ertalab soat 08:00 (CELERY_TIMEZONE = Asia/Tashkent).
    # O'tgan oy bo'yicha shaxsiy statistika har bir o'quvchi/o'qituvchiga.
    "oylik-statistika-har-oyning-birinchisida": {
        "task": "telegrambot.tasks.oylik_statistika_yubor",
        "schedule": crontab(day_of_month=1, hour=8, minute=0),
    },
    "kunlik-hisobot-har-5-daqiqada": {
        "task": "stats.tasks.send_daily_reports",
        "schedule": crontab(minute="*/5"),
    },
    "muddati-otganlarga-eslatma-har-kuni": {
        "task": "stats.tasks.send_overdue_reminders",
        "schedule": crontab(hour=10, minute=0),
    },
    "billing-sync-pending-payments": {
        "task": "billing.tasks.sync_pending_payments",
        "schedule": crontab(minute="*"),
    },
    "reytingni-har-hafta-yangila": {
        "task": "stats.tasks.update_library_ratings",
        "schedule": crontab(day_of_week=1, hour=3, minute=0),
    },
}
