"""Telegram bot orqali xabar yuborish (Django tomondan).

Celery vazifalari (jarima eslatmalari) va kutubxonachi jarimani to'lash
tasdiqlaganda shu yerdagi telegram_xabar_yubor() orqali o'quvchiga xabar
yuboriladi. To'g'ridan-to'g'ri Telegram Bot API ga boradi — alohida bot
jarayoni ishlamasa ham ishlaydi.
"""
import json
from html import escape
from urllib import error, request

from django.conf import settings


def telegram_escape(matn) -> str:
    """Matnni Telegram HTML parse_mode uchun xavfsizlashtiradi.

    O'quvchi ismi, izohi yoki kitob nomi kabi ma'lumotlar foydalanuvchi
    tomondan keladi. Ularni escape qilinmasdan `<b>`/`<` kabi teglar ichida
    qo'yilsa, Telegram 400 qaytaradi (yuborilgan xabar butunlay
    yo'qoladi). Shuning uchun dinamik qiymatlar shu funksiya orqali
    o'raladi; xabarning o'zidagi teglar esa qo'lda yoziladi.
    """
    return escape("" if matn is None else str(matn), quote=False)


def telegram_xabar_yubor(chat_id, matn, parse_mode="HTML"):
    """chat_id ga matn yuboradi. Muvaffaqiyatli bo'lsa True qaytaradi."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or not chat_id:
        return False
    if not isinstance(chat_id, int):
        try:
            chat_id = int(chat_id)
        except (TypeError, ValueError):
            return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps(
        {"chat_id": chat_id, "text": matn, "parse_mode": parse_mode},
        ensure_ascii=False,
    ).encode("utf-8")
    so_rov = request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with request.urlopen(so_rov, timeout=10) as javob:
            return javob.status == 200
    except (error.URLError, OSError):
        return False