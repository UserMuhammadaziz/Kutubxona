"""Health checks and heartbeats for the platform status view."""
from datetime import timedelta

from django.core.cache import cache
from django.db import connection
from django.utils import timezone

from .models import Heartbeat

# component -> max seconds between heartbeats before it counts as stale
HEARTBEAT_LIMITS = {"celery": 180, "bot_check": 1500}


def beat(name, **detail):
    Heartbeat.objects.update_or_create(
        name=name, defaults={"last_seen": timezone.now(), "detail": detail}
    )


def check_database():
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        return True, ""
    except Exception as exc:  # noqa: BLE001 - report any failure
        return False, str(exc)[:120]


def check_cache():
    try:
        cache.set("health:ping", "1", 10)
        return cache.get("health:ping") == "1", ""
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)[:120]


def liveness():
    """Cheap public check for uptime monitors."""
    db_ok, _ = check_database()
    cache_ok, _ = check_cache()
    return {"status": "ok" if db_ok else "down", "db": db_ok, "cache": cache_ok}


def heartbeat_status():
    now = timezone.now()
    seen = {h.name: h for h in Heartbeat.objects.all()}
    out = []
    for name, limit in HEARTBEAT_LIMITS.items():
        h = seen.get(name)
        if not h:
            out.append({"name": name, "status": "missing", "last_seen": None, "age_seconds": None, "limit_seconds": limit})
            continue
        age = int((now - h.last_seen).total_seconds())
        out.append(
            {
                "name": name,
                "status": "ok" if age <= limit else "stale",
                "last_seen": h.last_seen,
                "age_seconds": age,
                "limit_seconds": limit,
            }
        )
    return out


def bots_status():
    from telegrambot.models import TelegramBot

    stale_after = timezone.now() - timedelta(hours=1)
    rows = []
    for b in TelegramBot.objects.select_related("organization"):
        rows.append(
            {
                "organization": b.organization.nomi,
                "username": b.username,
                "state": b.holati,
                "webhook": b.webhook_ornatilgan,
                "last_check": b.oxirgi_tekshiruv,
                "last_error": b.oxirgi_xato,
                "stale": not b.oxirgi_tekshiruv or b.oxirgi_tekshiruv < stale_after,
            }
        )
    return rows
