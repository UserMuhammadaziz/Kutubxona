"""Link a staff member's Telegram account to their library membership.

The web profile asks for a one-time code and opens
`https://t.me/<bot>?start=staff_<code>`. Both bot flavours (the webhook
handler and the long-polling aiogram bot) end up in `link_staff`.
"""

from html import escape

from django.utils import timezone

from organization.models import Membership

STAFF_START_PREFIX = "staff_"


def deep_link(bot_username, code):
    if not bot_username or not code:
        return ""
    return f"https://t.me/{bot_username}?start={STAFF_START_PREFIX}{code}"


def code_from_start_payload(payload):
    """Return the link code from a /start payload, or "" if it is not a staff link."""
    payload = (payload or "").strip()
    if payload.startswith(STAFF_START_PREFIX):
        return payload[len(STAFF_START_PREFIX):]
    return ""


def link_staff(organization, code, telegram_id):
    """Bind `telegram_id` to the membership holding `code`.

    Returns (membership, message). `membership` is None on failure and
    `message` then explains why, in Uzbek, ready to send to the user.
    """
    code = (code or "").strip()
    if not code or not telegram_id:
        return None, "Kod yaroqsiz yoki muddati o'tgan."
    membership = (
        Membership.objects.select_related("user")
        .filter(
            organization=organization,
            link_code=code,
            link_code_expires__gt=timezone.now(),
            faol=True,
        )
        .first()
    )
    if not membership:
        return None, (
            "Kod yaroqsiz yoki muddati o'tgan. Saytdagi profilingizdan "
            "«Telegram botga ulanish» tugmasini qayta bosing."
        )
    taken = (
        Membership.objects.filter(organization=organization, telegram_id=telegram_id)
        .exclude(pk=membership.pk)
        .exists()
    )
    if taken:
        return None, "Bu Telegram akkaunt shu kutubxonadagi boshqa xodimga bog'langan."
    membership.telegram_id = telegram_id
    membership.link_code = ""
    membership.link_code_expires = None
    membership.save(update_fields=["telegram_id", "link_code", "link_code_expires"])
    name = membership.user.full_name or membership.user.username
    return membership, (
        f"✅ Telegram ulandi. Xush kelibsiz, {escape(name)}!\n\n"
        "Endi kunlik hisobotlar, yangiliklar va muhim xabarlar shu botga keladi."
    )


def unlink_staff(membership):
    membership.telegram_id = None
    membership.link_code = ""
    membership.link_code_expires = None
    membership.save(update_fields=["telegram_id", "link_code", "link_code_expires"])
