"""Book reviews: read what others thought, rate a returned book, write an opinion.

Callback data matches the Django webhook handler (`rv_list`, `rv_new`,
`rv_rate`, `rv_skip`), so the invite sent after a return works in both bots.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from api_client import ApiXato, api
from keyboards import asosiy_tugmalar_klaviaturasi, rating_keyboard
from states import ReviewText
from utils import x

router = Router(name="reviews")

NOT_ALLOWED = "Fikrni kitobni o'qib, kutubxonaga qaytargandan keyin qoldirish mumkin."
SAVED = "✅ Fikringiz saqlandi. Rahmat! Boshqa kitobxonlar uni kitob kartasida ko'radi."


def _parts(data: str):
    parts = data.split(":")
    book = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    rating = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() and 1 <= int(parts[2]) <= 5 else None
    return book, rating


def _list_text(data: dict) -> str:
    title = x(data.get("book_title"))
    summary = data.get("summary") or {}
    if not summary.get("count"):
        return f"💬 <b>{title}</b>\n\nHali fikr qoldirilmagan. Birinchi bo'lib siz yozing!"
    lines = [f"💬 <b>{title}</b>", f"⭐ {summary['avg']} / 5 · {summary['count']} ta baho", ""]
    for review in data.get("reviews") or []:
        lines.append(f"{'⭐' * int(review['rating'])} <b>{x(review['author'])}</b>")
        if review.get("text"):
            lines.append(x(review["text"]))
        lines.append("")
    return "\n".join(lines).strip()


def _write_button(book: int, mine: bool) -> InlineKeyboardMarkup:
    label = "✏️ Fikrimni o'zgartirish" if mine else "✍️ Fikr qoldirish"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=label, callback_data=f"rv_new:{book}")]])


async def _reply(callback: CallbackQuery, text: str, markup=None):
    if callback.message is not None:
        await callback.message.answer(text, reply_markup=markup)
    else:
        await callback.bot.send_message(callback.from_user.id, text, reply_markup=markup)


@router.callback_query(F.data.startswith("rv_list:"))
async def review_list(callback: CallbackQuery):
    book, _ = _parts(callback.data)
    if book is None:
        await callback.answer()
        return
    try:
        data = await api.reviews(book, callback.from_user.id)
    except ApiXato as e:
        await callback.answer(e.detail, show_alert=True)
        return
    markup = _write_button(book, bool(data.get("mine"))) if data.get("can_review") else None
    await _reply(callback, _list_text(data), markup)
    await callback.answer()


@router.callback_query(F.data.startswith("rv_new:"))
async def review_new(callback: CallbackQuery):
    book, _ = _parts(callback.data)
    if book is None:
        await callback.answer()
        return
    try:
        data = await api.reviews(book, callback.from_user.id)
    except ApiXato as e:
        await callback.answer(e.detail, show_alert=True)
        return
    if not data.get("can_review"):
        await callback.answer(NOT_ALLOWED, show_alert=True)
        return
    await _reply(
        callback, f"✍️ <b>{x(data.get('book_title'))}</b> kitobiga 1 dan 5 gacha baho bering:", rating_keyboard(book)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rv_rate:"))
async def review_rate(callback: CallbackQuery, state: FSMContext):
    book, rating = _parts(callback.data)
    if book is None or rating is None:
        await callback.answer()
        return
    await state.set_state(ReviewText.text)
    await state.update_data(review_book=book, review_rating=rating)
    skip = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Izohsiz saqlash", callback_data=f"rv_skip:{book}:{rating}")]]
    )
    await _reply(
        callback,
        f"Bahoyingiz: {'⭐' * rating}\n\nEndi kitob haqida qisqacha fikringizni yozing "
        "(nima yoqdi, kimga tavsiya qilasiz). Izohsiz saqlash uchun tugmani bosing.",
        skip,
    )
    await callback.answer()


async def _save(target: Message, telegram_id: int, book: int, rating: int, text: str = "") -> None:
    try:
        await api.save_review(book, telegram_id, rating, text)
    except ApiXato as e:
        await target.answer(e.detail, reply_markup=asosiy_tugmalar_klaviaturasi())
        return
    await target.answer(SAVED, reply_markup=asosiy_tugmalar_klaviaturasi())


@router.callback_query(F.data.startswith("rv_skip:"))
async def review_skip(callback: CallbackQuery, state: FSMContext):
    book, rating = _parts(callback.data)
    await state.clear()
    if book is None or rating is None or callback.message is None:
        await callback.answer()
        return
    await _save(callback.message, callback.from_user.id, book, rating)
    await callback.answer()


@router.message(ReviewText.text, F.text, ~F.text.startswith("/"))
async def review_text(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    book, rating = data.get("review_book"), data.get("review_rating")
    if not book or not rating:
        return
    await _save(message, message.from_user.id, book, rating, message.text[:1000])
