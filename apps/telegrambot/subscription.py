"""Mandatory channel subscription for a library's bot.

A library may name a Telegram channel in its profile. Readers (and anyone
not yet registered) must be subscribed before the bot serves them; linked
staff are exempt. The check fails open: if Telegram cannot answer (bot
removed from the channel, network error), users are let through so a
broken setting never locks the whole library out of its bot.
"""

import logging
import re

from django.core.cache import cache
from rest_framework.exceptions import ValidationError

from config.telegram import _token_ol
from organization.models import Membership

from .client import TelegramAPIError, export_chat_invite_link, get_chat, get_chat_member, get_me

logger = logging.getLogger(__name__)

CHECK_CALLBACK = "sub_check"
SUBSCRIBED_STATUSES = {"creator", "administrator", "member"}
POSITIVE_CACHE_SECONDS = 10 * 60

_USERNAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{3,31}$")
_LINK_RE = re.compile(r"^(?:https?://)?(?:t\.me|telegram\.me)/([A-Za-z0-9_]+)/?$", re.IGNORECASE)


def normalize_channel(raw):
    """Turn "@name", "name", "t.me/name" or "-100123" into a chat_id for the Bot API."""
    value = (raw or "").strip()
    if not value:
        raise ValidationError("Kanalni kiriting.")
    if re.fullmatch(r"-100\d{5,}", value):
        return value
    match = _LINK_RE.match(value)
    if match:
        value = match.group(1)
    value = value.lstrip("@")
    if value.startswith("+") or value.lower() == "joinchat":
        raise ValidationError(
            "Yopiq kanal havolasi emas, kanal ID sini kiriting (masalan: -1001234567890)."
        )
    if not _USERNAME_RE.match(value):
        raise ValidationError("Kanal nomi noto'g'ri. Masalan: @kutubxona_kanali")
    return f"@{value}"


def resolve_channel(organization, raw):
    """Check the channel through the library's bot and return what to store.

    Raises ValidationError with a librarian-friendly message when the bot is
    not connected, the channel is not found or the bot is not its admin.
    """
    chat_ref = normalize_channel(raw)
    token = _token_ol(organization)
    if not token:
        raise ValidationError("Avval kutubxonaning Telegram botini ulang.")
    try:
        chat = get_chat(token, chat_ref)
    except TelegramAPIError:
        raise ValidationError(
            "Kanal topilmadi. Nomini tekshiring va botni kanalga administrator qilib qo'shing."
        )
    if chat.get("type") not in ("channel", "supergroup"):
        raise ValidationError("Bu kanal yoki guruh emas.")
    try:
        me = get_me(token)
        member = get_chat_member(token, chat["id"], me["id"])
    except TelegramAPIError:
        raise ValidationError("Bot kanal a'zolarini ko'ra olmayapti. Botni administrator qiling.")
    if member.get("status") not in ("administrator", "creator"):
        raise ValidationError(
            f"@{me.get('username', 'bot')} kanalda administrator emas. Uni administrator qilib qo'shing."
        )
    username = chat.get("username") or ""
    url = f"https://t.me/{username}" if username else chat.get("invite_link") or ""
    if not url:
        try:
            url = export_chat_invite_link(token, chat["id"])
        except TelegramAPIError:
            raise ValidationError(
                "Yopiq kanal uchun botga «Havola orqali taklif qilish» huquqini bering."
            )
    return {
        "subscription_channel": f"@{username}" if username else str(chat["id"]),
        "subscription_channel_id": int(chat["id"]),
        "subscription_channel_title": (chat.get("title") or "")[:255],
        "subscription_channel_url": url[:255],
    }


def _cache_key(organization, telegram_id):
    return f"tg-sub:{organization.pk}:{organization.subscription_channel_id}:{telegram_id}"


def is_subscribed(organization, telegram_id, fresh=False):
    key = _cache_key(organization, telegram_id)
    if not fresh and cache.get(key):
        return True
    token = _token_ol(organization)
    if not token:
        return True
    try:
        member = get_chat_member(token, organization.subscription_channel_id, telegram_id, timeout=5)
    except TelegramAPIError as error:
        description = (error.description or "").lower()
        if "user not found" in description or "participant_id_invalid" in description:
            cache.delete(key)
            return False
        logger.warning("Subscription check failed for org %s: %s", organization.pk, error.description)
        return True  # fail open
    status = member.get("status")
    ok = status in SUBSCRIBED_STATUSES or (status == "restricted" and member.get("is_member"))
    if ok:
        cache.set(key, True, POSITIVE_CACHE_SECONDS)
    else:
        cache.delete(key)  # a fresh "left" must not be hidden by an older positive answer
    return ok


def subscription_gate(organization, telegram_id, fresh=False):
    """Return None when the user may use the bot, else {"title", "url"} of the channel."""
    if organization is None or not organization.subscription_channel_id or not telegram_id:
        return None
    is_staff = Membership.objects.filter(
        organization=organization, telegram_id=telegram_id, faol=True
    ).exists()
    if is_staff or is_subscribed(organization, telegram_id, fresh=fresh):
        return None
    return {
        "title": organization.subscription_channel_title or organization.subscription_channel,
        "url": organization.subscription_channel_url,
    }


def gate_text(gate):
    from html import escape

    return (
        "📢 Botdan foydalanish uchun kutubxonamiz kanaliga obuna bo'ling:\n"
        f"<b>{escape(gate['title'])}</b>\n\n"
        "Obuna bo'lgach, «✅ Obuna bo'ldim» tugmasini bosing."
    )


def gate_keyboard(gate):
    rows = []
    if gate.get("url"):
        rows.append([{"text": "📢 Kanalga obuna bo'lish", "url": gate["url"]}])
    rows.append([{"text": "✅ Obuna bo'ldim", "callback_data": CHECK_CALLBACK}])
    return {"inline_keyboard": rows}
