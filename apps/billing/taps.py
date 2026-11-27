"""Minimal client for taps.so donation pages (the platform's payment gateway).

Flow: create a donation for the exact amount -> the payer pays on
`checkoutUrl` -> we poll `/donations/<id>/status` until it is Paid. The API
has no key: a payment is trusted only through the donation id we stored and
the amount Taps reports for it.
"""

import json
import re
from urllib import error as urlerror
from urllib import request as urlrequest

from django.conf import settings

TIMEOUT = 15

# Taps provider ids (public/donation-pages/<slug>/payment-providers).
# The card provider (55) is left out: it sends the payer to an ad-filled page.
METHODS = {
    "click": (25, "Click"),
    "payme": (26, "Payme"),
    "uzum": (24, "Uzum Bank"),
    "alif": (32, "Alif"),
    "xazna": (37, "Xazna"),
    "paynet": (33, "Paynet"),
    "beepul": (38, "Beepul"),
    "oson": (39, "Oson"),
    "anorbank": (36, "Anorbank"),
    "asiaalliancebank": (35, "Asia Alliance Bank"),
    "trastpay": (40, "TrastPay"),
}

_DEAD = re.compile(r"cancel|fail|reject|expire", re.IGNORECASE)


class TapsError(Exception):
    pass


def _api():
    return f"https://api.taps.so/api/profiles/{settings.TAPS_PROFILE_ID}/donations"


def _call(method, url, payload=None, headers=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urlrequest.Request(
        url,
        data=body,
        method=method,
        headers={
            "content-type": "application/json",
            "accept": "application/json",
            "user-agent": "Mozilla/5.0 (compatible; KutubxonaBilling/1.0)",
            **(headers or {}),
        },
    )
    status = 0
    try:
        with urlrequest.urlopen(req, timeout=TIMEOUT) as response:
            status = response.status
            raw = response.read()
    except urlerror.HTTPError as http_error:
        status = http_error.code
        raw = http_error.read()
    except (urlerror.URLError, OSError) as network_error:
        raise TapsError(f"taps: {network_error.__class__.__name__}") from network_error
    try:
        data = json.loads(raw.decode("utf-8"))
    except ValueError:
        data = None
    if status >= 400 or not isinstance(data, dict) or not data.get("isSuccess"):
        err = data.get("error") if isinstance(data, dict) else None
        message = err.get("message") if isinstance(err, dict) else err
        raise TapsError(f"taps {status}: {message or 'error'}")
    return data.get("data") or {}


def create_donation(*, method, amount, note):
    provider_id = METHODS[method][0]
    slug = settings.TAPS_SLUG
    return _call(
        "POST",
        _api(),
        headers={"origin": "https://taps.uz"},
        payload={
            "providerId": provider_id,
            "amount": int(amount),
            "source": "rahmat",
            "donater": "",
            "isAnonymous": True,
            # Taps accepts only a return URL under its own domain.
            "returnUrl": f"https://taps.so/{slug}/donation-result?profileId={settings.TAPS_PROFILE_ID}",
            "notes": note,
            "payerPayCommission": False,
        },
    )


def donation_status(donation_id):
    return _call("GET", f"{_api()}/{donation_id}/status")


def is_paid(data):
    status = str(data.get("status") or "")
    return status == "Paid" or (data.get("paidTime") is not None and not _DEAD.search(status))


def is_dead(data):
    return bool(_DEAD.search(str(data.get("status") or "")))


def paid_amount(data):
    """What the payer paid in total; commission is ours, so donateAmount may be lower."""
    value = data.get("amount") if data.get("amount") is not None else data.get("donateAmount")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
