"""Normalise UTM tags, click ids and referrers into one (source, medium) pair."""
import re
from datetime import datetime
from urllib.parse import urlsplit

from django.utils import timezone

UTM_FIELDS = ("source", "medium", "campaign", "term", "content")
FIELD_LIMITS = {"source": 80, "medium": 80, "campaign": 120, "term": 120, "content": 120}
VISITOR_ID = re.compile(r"^[A-Za-z0-9-]{8,40}$")
# Click ids that ad networks append: they mean a paid click from that network.
CLICK_IDS = {"gclid": ("google", "cpc"), "yclid": ("yandex", "cpc"), "fbclid": ("facebook", "social")}

# Host suffix -> (source, medium) for visits without UTM tags.
REFERRERS = [
    (("google.",), "google", "organic"),
    (("yandex.", "ya.ru"), "yandex", "organic"),
    (("bing.com",), "bing", "organic"),
    (("duckduckgo.com",), "duckduckgo", "organic"),
    (("t.me", "telegram.org", "telegram.me", "web.telegram.org"), "telegram", "social"),
    (("instagram.com", "l.instagram.com"), "instagram", "social"),
    (("facebook.com", "fb.com", "m.facebook.com", "l.facebook.com"), "facebook", "social"),
    (("youtube.com", "youtu.be"), "youtube", "social"),
    (("tiktok.com",), "tiktok", "social"),
    (("linkedin.com", "lnkd.in"), "linkedin", "social"),
    (("x.com", "twitter.com", "t.co"), "x", "social"),
]


def _clean(value, limit):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit]


def referrer_host(referrer, own_host=""):
    try:
        host = (urlsplit(str(referrer or "")).hostname or "").lower()
    except ValueError:
        return ""
    host = host.removeprefix("www.")
    if not host or (own_host and host == own_host.lower().removeprefix("www.")):
        return ""
    return host[:120]


def classify_referrer(host):
    for suffixes, source, medium in REFERRERS:
        for suffix in suffixes:
            if suffix.endswith("."):
                if re.search(rf"(^|\.){re.escape(suffix)}[a-z.]+$", host):
                    return source, medium
            elif host == suffix or host.endswith("." + suffix):
                return source, medium
    return host, "referral"


def normalise(raw, own_host=""):
    """Turn a client payload into clean Visit/attribution fields."""
    raw = raw if isinstance(raw, dict) else {}
    data = {f: _clean(raw.get(f) or raw.get(f"utm_{f}"), FIELD_LIMITS[f]) for f in UTM_FIELDS}
    data["source"] = data["source"].lower()
    data["medium"] = data["medium"].lower()
    data["referrer_host"] = referrer_host(raw.get("referrer"), own_host)
    path = _clean(raw.get("path") or raw.get("landing_path"), 200)
    data["landing_path"] = path if path.startswith("/") else ""
    click = next((key for key in CLICK_IDS if raw.get(key)), "")
    click = click or (raw.get("click_id") if raw.get("click_id") in CLICK_IDS else "")
    data["click_id"] = click
    if not data["source"]:
        if click:
            data["source"], medium = CLICK_IDS[click]
            data["medium"] = data["medium"] or medium
        elif data["referrer_host"]:
            data["source"], medium = classify_referrer(data["referrer_host"])
            data["medium"] = data["medium"] or medium
        else:
            data["source"], data["medium"] = "direct", data["medium"] or "none"
    visitor = str(raw.get("visitor_id") or "")
    data["visitor_id"] = visitor if VISITOR_ID.fullmatch(visitor) else ""
    return data


def parse_time(value):
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if timezone.is_naive(moment):
        moment = timezone.make_aware(moment)
    return moment if moment <= timezone.now() else None


def record_signup(organization, payload, own_host=""):
    """Store first/last touch for a new organization. Never breaks signup."""
    from .models import SignupAttribution, Visit

    payload = payload if isinstance(payload, dict) else {}
    first = normalise(payload.get("first") or payload, own_host)
    last = normalise(payload.get("last") or payload.get("first") or payload, own_host)
    first_seen = parse_time((payload.get("first") or {}).get("at") if isinstance(payload.get("first"), dict) else None)
    visitor = first["visitor_id"] or last["visitor_id"]
    if visitor:
        earliest = Visit.objects.filter(visitor_id=visitor).order_by("created_at").first()
        if earliest and (first_seen is None or earliest.created_at < first_seen):
            first_seen = earliest.created_at
            if first["source"] == "direct":
                first.update({f: getattr(earliest, f) for f in (*UTM_FIELDS, "referrer_host", "landing_path", "click_id")})
    return SignupAttribution.objects.create(
        organization=organization,
        visitor_id=visitor,
        first_seen_at=first_seen,
        last_source=last["source"],
        last_medium=last["medium"],
        last_campaign=last["campaign"],
        **{k: v for k, v in first.items() if k != "visitor_id"},
    )
