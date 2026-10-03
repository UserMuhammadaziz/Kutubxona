"""Bot yordamchilari: xabarni xatosiz tahrirlash va matnni xavfsizlashtirish.

Telegram'da `edit_text` quyidagi holatlarda xato beradi:
  * matn o'zgarmagan ("message is not modified");
  * xabar juda eskirgan ("message to edit not found").

Foydalanuvchi tugmani ikki marta bossa yoki eski xabordagi tugmani bossa
butun oqim `TelegramBadRequest` bilan uzilib ketadi — foydalanuvchi hech narsa
ko'rmaydi. `xabarni_tahrirlash` bu holatlarda xatosiz o'tadi.

Bot butun bo'ylab `parse_mode=HTML` bilan ishlaydi (`main.py`), shuning
uchun kitob nomi, muallif, tavsif, API xato matni kabi dinamik qiymatlar
`&`, `<`, `>` belgilarini o'z ichiga olsa, Telegram butun xabarni
tahlil qila olmaydi va `can't parse entities` xatosi beradi. `x()`
bunday qiymatlarni escape qiladi.
"""
import logging
from html import escape

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger(__name__)


def x(qiymat) -> str:
    """Qiymatni Telegram HTML uchun xavfsizlashtiradi (`None` → "")."""
    if qiymat is None:
        return ""
    return escape(str(qiymat), quote=False)


async def xabarni_tahrirlash(
    xabar: Message | CallbackQuery | None,
    matn: str,
    reply_markup=None,
) -> bool:
    """`message.edit_text` ning xatolarsiz versiyasi.

    CallbackQuery uchun avval undagi xabar, keyin undan o'zi tahrirlanadi.
    Qaytaradi: matn haqiqatan yangilandi (True) yoki o'zgartirilmadi (False).
    """
    if xabar is None:
        return False

    if isinstance(xabar, CallbackQuery):
        if xabar.message is None:
            # Inline xabarning o'zi yo'q (masalan, juda eski xabar) —
            # yangisini yuborish ham imkonsiz, shuning uchun javob beramiz.
            await xabar.answer("Bu xabar allaqon eskirgan. /start bosing.")
            return False
        xabar = xabar.message

    try:
        await xabar.edit_text(matn, reply_markup=reply_markup)
    except TelegramBadRequest as xato:
        if "message is not modified" in str(xato).lower():
            return False
        if "message to edit not found" in str(xato).lower():
            await xabar.answer(
                "Bu xabar allaqon eskirgan. Asosiy menyudan qayta bosing."
            )
            return False
        logger.warning("xabar tahrirlanmadi: %s", xato)
        return False
    return True