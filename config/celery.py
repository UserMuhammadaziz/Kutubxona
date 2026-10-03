import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("kutubxona")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
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
}
