"""Telegram xabar yuborish (Django tomondan).

SaaS rejimida har bir kutubxona o'z boti orqali xabar yuboradi. Eski
bitta-kutubxonali rejim (yoki bot UI orqali ulanmagan, lekin `.env` da
ishlab turgan bot) uchun `settings.TELEGRAM_BOT_TOKEN` fallback bo'lib
qoladi. Global token faqat **bitta** faol tashkilot bo'lganda ishlatiladi —
aks holda boshqa kutubxona nomidan xabar ketardi.
"""

from html import escape

from django.conf import settings


def telegram_escape(matn) -> str:
    return escape("" if matn is None else str(matn), quote=False)


def _global_token_mumkin() -> bool:
    """Legacy (bitta kutubxonali) o'rnatishda .env tokenidan foydalanish mumkinmi?

    Ko'p kutubxonali SaaS'da global token ishlatilsa, xabar boshqa
    kutubxona nomidan ketadi. Shuning uchun faqat **bitta** faol tashkilot
    bo'lganda va token haqiqatda sozlanganda ruxsat etiladi.
    """
    if not getattr(settings, "TELEGRAM_BOT_TOKEN", ""):
        return False
    try:
        from organization.models import Organization

        return Organization.objects.filter(status=Organization.HOLAT_ACTIVE).count() <= 1
    except Exception:
        return False


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
            bot = None
        if bot is not None and bot.holati == "ulangan" and organization.faol:
            try:
                return bot.get_token()
            except Exception:
                pass
        # Bot UI orqali ulanmagan, lekin server .env da ishlab turgan
        # (polling) bot bor — legacy rejimda shu token bilan yuboramiz.
        if _global_token_mumkin():
            return settings.TELEGRAM_BOT_TOKEN
        return ""
    return settings.TELEGRAM_BOT_TOKEN


def telegram_xabar_yubor(
    chat_id, matn, parse_mode="HTML", organization=None, bot=None, reply_markup=None
):
    """chat_id ga xabar yuboradi. Muvaffaqiyatli bo'lsa True.

    `organization` berilgan bo'lsa, avval shu kutubxonaning ulangan boti,
    bo'lmasa — faqat bitta kutubxona bo'lganda `.env` dagi global token
    ishlatiladi. Ikkalasi ham yo'q bo'lsa False qaytadi.
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
