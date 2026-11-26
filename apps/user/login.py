"""Resolve what a person typed in the login field to a real username.

The field accepts a username or a phone number. Long numeric usernames
must keep working, so the exact username always wins over phone parsing.
"""
import re

from django.contrib.auth import get_user_model

PHONE_PREFIX = "998"


def phone_candidates(raw: str) -> list[str]:
    """Canonical "+998XXXXXXXXX" forms a phone-looking input may mean."""
    if not re.fullmatch(r"[+\d][\d\s\-()+]*", raw):
        return []
    digits = re.sub(r"\D", "", raw)
    if digits.startswith(PHONE_PREFIX):
        digits = digits[len(PHONE_PREFIX):]
    elif len(digits) == 10 and digits.startswith("0"):
        digits = digits[1:]
    return [f"+{PHONE_PREFIX}{digits}"] if len(digits) == 9 else []


def resolve_username(raw) -> str:
    value = str(raw or "").strip()
    if not value:
        return value
    users = get_user_model().objects
    if users.filter(username=value).exists():
        return value
    match = users.filter(username__iexact=value).values_list("username", flat=True).first()
    if match:
        return match
    for phone in phone_candidates(value):
        match = (
            users.filter(username__in=[phone, phone[1:]]).values_list("username", flat=True).first()
            or users.filter(telefon=phone, is_active=True).values_list("username", flat=True).first()
        )
        if match:
            return match
    return value
