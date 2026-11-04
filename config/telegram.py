"""Telegram xabar yuborish (Django tomondan).

SaaS rejimida har bir kutubxona o'z boti orqali xabar yuboradi. Eski
bitta-kutubxonali rejim uchun `settings.TELEGRAM_BOT_TOKEN` fallback bo'lib
qoladi, lekin `organization` berilganda global token **hech qachon**
ishlatilmaydi — aks holda boshqa kutubxona nomidan xabar ketardi.
"""

from html import escape

from django.conf import settings


def telegram_escape(matn) -> str:
    return escape("" if matn is None else str(matn), quote=False)


def _token_ol(organization=None, bot=None):
    if bot is not None:
        try:
            return bot.get_token()
        except Exception:
            return ""
    if organization is not None:
        try:
            bot = organization.telegram_bot
        except Exception:
            return ""
        if bot.holati != "ulangan" or not organization.faol:
            return ""
        try:
            return bot.get_token()
        except Exception:
            return ""
    return settings.TELEGRAM_BOT_TOKEN


def telegram_xabar_yubor(
    chat_id, matn, parse_mode="HTML", organization=None, bot=None, reply_markup=None
):
    """chat_id ga xabar yuboradi. Muvaffaqiyatli bo'lsa True.

    `organization` berilgan bo'lsa, faqat shu kutubxonaning ulangan boti
    ishlatiladi. Bot ulanmagan bo'lsa False qaytadi (global tokenga
    tushmaydi).
    """
    token = _token_ol(organization=organization, bot=bot)
    if not token or not chat_id:
        return False
    if not isinstance(chat_id, int):
        try:
            chat_id = int(chat_id)
        except (TypeError, ValueError):
            return False
    try:
        from telegrambot.client import send_message

        send_message(token, chat_id, matn, reply_markup=reply_markup, parse_mode=parse_mode)
        return True
    except Exception:
        return False
