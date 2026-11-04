import re

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .client import (
    TelegramAPIError,
    delete_webhook,
    get_me,
    get_webhook_info,
    send_message,
    set_webhook,
)
from .models import TelegramBot

TOKEN_RE = re.compile(r"^\d{6,}:[A-Za-z0-9_-]{30,}$")


def _webhook_url(bot):
    return (
        f"{settings.TELEGRAM_WEBHOOK_BASE_URL.rstrip('/')}"
        f"/api/telegram/webhook/{bot.webhook_path}/"
    )


def botni_ol(organization):
    return TelegramBot.objects.filter(organization=organization).first()


def botni_ulash(organization, token):
    """Tokenni tekshiradi, shifrlaydi va webhook o'rnatadi.

    Xato bo'lsa ham token saqlanmaydi — noto'g'ri token bilan kutubxona
    botini iflos qilib qo'ymaslik uchun avval Telegram getMe chaqiriladi.
    """
    token = (token or "").strip()
    if not TOKEN_RE.match(token):
        raise ValidationError({"token": "Telegram bot tokeni formati noto'g'ri."})

    try:
        info = get_me(token)
    except TelegramAPIError as xato:
        raise ValidationError({"token": f"Token tekshirilmadi: {xato.description}"})

    bot_id = int(info["id"])
    boshqa = TelegramBot.objects.filter(telegram_bot_id=bot_id).exclude(
        organization=organization
    )
    if boshqa.exists():
        raise ValidationError(
            {"token": "Bu bot boshqa kutubxonaga ulangan. Har bir kutubxonaga alohida bot kerak."}
        )

    bot = TelegramBot.objects.filter(organization=organization).first()
    if bot is None:
        bot = TelegramBot(
            organization=organization,
            telegram_bot_id=bot_id,
            webhook_path=TelegramBot.yangi_webhook_path(),
            webhook_secret=TelegramBot.yangi_secret(),
        )
    else:
        bot.telegram_bot_id = bot_id
        if not bot.webhook_path:
            bot.webhook_path = TelegramBot.yangi_webhook_path()
        if not bot.webhook_secret:
            bot.webhook_secret = TelegramBot.yangi_secret()
    bot.username = info.get("username", "")
    bot.set_token(token)
    bot.holati = "ulanmoqda"
    bot.oxirgi_xato = ""
    bot.save()

    try:
        set_webhook(token, _webhook_url(bot), bot.webhook_secret)
    except TelegramAPIError as xato:
        bot.holati = "xato"
        bot.webhook_ornatilgan = False
        bot.oxirgi_xato = str(xato.description)[:255]
        bot.oxirgi_tekshiruv = timezone.now()
        bot.save(update_fields=["holati", "webhook_ornatilgan", "oxirgi_xato", "oxirgi_tekshiruv"])
        raise ValidationError(
            {
                "token": (
                    "Bot tokeni to'g'ri, lekin webhook o'rnatilmadi: "
                    f"{xato.description}. HTTPS manzil kerak."
                )
            }
        )

    bot.holati = "ulangan"
    bot.webhook_ornatilgan = True
    bot.oxirgi_tekshiruv = timezone.now()
    bot.save(
        update_fields=[
            "holati",
            "webhook_ornatilgan",
            "oxirgi_tekshiruv",
            "telegram_bot_id",
            "username",
            "token_encrypted",
            "webhook_path",
            "webhook_secret",
        ]
    )
    return bot


def botni_tekshirish(bot):
    try:
        info = get_me(bot.get_token())
        bot.username = info.get("username", bot.username)
        bot.telegram_bot_id = int(info["id"])
        bot.holati = "ulangan" if bot.webhook_ornatilgan else "uzilgan"
        bot.oxirgi_xato = ""
        try:
            webhook = get_webhook_info(bot.get_token())
            bot.webhook_ornatilgan = bool(webhook.get("url"))
        except TelegramAPIError:
            pass
    except TelegramAPIError as xato:
        bot.holati = "xato"
        bot.oxirgi_xato = str(xato.description)[:255]
    bot.oxirgi_tekshiruv = timezone.now()
    bot.save()
    return bot


def botni_uzish(bot):
    try:
        delete_webhook(bot.get_token())
    except TelegramAPIError:
        pass
    bot.holati = "uzilgan"
    bot.webhook_ornatilgan = False
    bot.oxirgi_tekshiruv = timezone.now()
    bot.save(update_fields=["holati", "webhook_ornatilgan", "oxirgi_tekshiruv"])


def xabar_yubor(bot, chat_id, matn, reply_markup=None):
    if not bot or bot.holati != "ulangan" or not bot.organization.faol:
        return False
    try:
        send_message(bot.get_token(), chat_id, matn, reply_markup=reply_markup)
        return True
    except TelegramAPIError:
        return False


def organizatsiya_xabari(organization, chat_id, matn, reply_markup=None):
    bot = botni_ol(organization)
    return xabar_yubor(bot, chat_id, matn, reply_markup=reply_markup)


def webhookni_qayta_ornat(bot):
    set_webhook(bot.get_token(), _webhook_url(bot), bot.webhook_secret)
    bot.webhook_ornatilgan = True
    bot.holati = "ulangan"
    bot.oxirgi_xato = ""
    bot.save(update_fields=["webhook_ornatilgan", "holati", "oxirgi_xato"])
    return bot


def yangilanishni_qabul_qil(bot, update):
    from .handler import handle_update

    return handle_update(bot, update)
