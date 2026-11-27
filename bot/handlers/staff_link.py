"""/start staff_<code>: link a staff member's Telegram (code comes from the web profile)."""
import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from api_client import ApiXato, api
from utils import x

router = Router(name="staff_link")
logger = logging.getLogger(__name__)

STAFF_START_PREFIX = "staff_"


@router.message(CommandStart(deep_link=True, magic=F.args.startswith(STAFF_START_PREFIX)))
async def staff_link(message: Message, state: FSMContext):
    await state.clear()
    code = (message.text or "").split(maxsplit=1)[1][len(STAFF_START_PREFIX):]
    try:
        result = await api.staff_link(code, message.from_user.id)
    except ApiXato as e:
        logger.warning("Staff link failed: %s", e.detail)
        await message.answer(f"Ulab bo'lmadi: {x(e.detail)}")
        return
    # The backend message is already HTML-escaped.
    await message.answer(result.get("message") or "Tayyor.")
