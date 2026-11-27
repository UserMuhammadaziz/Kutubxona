"""Book reviews: who may write one, saving it, and what readers see."""

from django.db.models import Avg, BooleanField, Case, Count, Value, When

from berish.models import Berish

from .models import Review

MAX_TEXT = 1000
PUBLIC_LIMIT = 5


def has_read(reader, book):
    """Only someone who borrowed the book and brought it back can review it."""
    return Berish.objects.filter(
        organization=book.organization, oquvchi=reader, kitob=book, qaytarilgan_sana__isnull=False
    ).exists()


def save_review(reader, book, rating, text=""):
    rating = int(rating)
    if not 1 <= rating <= 5:
        raise ValueError("rating")
    review, _ = Review.objects.update_or_create(
        book=book,
        reader=reader,
        defaults={"organization": book.organization, "rating": rating, "text": (text or "").strip()[:MAX_TEXT]},
    )
    return review


def summary(book):
    data = Review.objects.filter(book=book, is_hidden=False).aggregate(avg=Avg("rating"), count=Count("id"))
    return {"avg": round(data["avg"], 1) if data["avg"] else None, "count": data["count"]}


def public_reviews(book, limit=PUBLIC_LIMIT):
    """Visible reviews with text first, newest first."""
    return list(
        Review.objects.filter(book=book, is_hidden=False)
        .select_related("reader")
        .annotate(empty=Case(When(text="", then=Value(True)), default=Value(False), output_field=BooleanField()))
        .order_by("empty", "-updated_at")[:limit]
    )


def reader_label(reader):
    """First name and class/subject only: full names stay private."""
    name = (reader.fish or "").split()
    first = name[1] if len(name) > 1 else (name[0] if name else "Kitobxon")
    extra = reader.kasb if reader.rol == "oqituvchi" else reader.sinf
    return f"{first} ({extra})" if extra else first


def stars(rating):
    return "⭐" * int(rating)


def telegram_text(book, reviews, info):
    from html import escape

    if not info["count"]:
        return f"💬 <b>{escape(book.nomi)}</b>\n\nHali fikr qoldirilmagan. Birinchi bo'lib siz yozing!"
    lines = [f"💬 <b>{escape(book.nomi)}</b>", f"⭐ {info['avg']} / 5 · {info['count']} ta baho", ""]
    for review in reviews:
        lines.append(f"{stars(review.rating)} <b>{escape(reader_label(review.reader))}</b>")
        if review.text:
            lines.append(escape(review.text))
        lines.append("")
    return "\n".join(lines).strip()


# Telegram callback data shared by the webhook handler and the aiogram bot.
def rating_keyboard(book_id):
    """Five buttons 1..5 → `rv_rate:<book>:<n>`."""
    return {
        "inline_keyboard": [
            [{"text": f"{n}⭐", "callback_data": f"rv_rate:{book_id}:{n}"} for n in range(1, 6)]
        ]
    }


def skip_keyboard(book_id, rating):
    return {"inline_keyboard": [[{"text": "Izohsiz saqlash", "callback_data": f"rv_skip:{book_id}:{rating}"}]]}


RATE_PROMPT = "✍️ <b>{title}</b> kitobiga 1 dan 5 gacha baho bering:"
TEXT_PROMPT = (
    "Bahoyingiz: {stars}\n\nEndi kitob haqida qisqacha fikringizni yozing "
    "(nima yoqdi, kimga tavsiya qilasiz). Izohsiz saqlash uchun tugmani bosing."
)
SAVED = "✅ Fikringiz saqlandi. Rahmat! Boshqa kitobxonlar uni kitob kartasida ko'radi."
NOT_ALLOWED = "Fikrni kitobni o'qib, kutubxonaga qaytargandan keyin qoldirish mumkin."


def invite_after_return(berish):
    """Ask the reader to rate the book they have just returned."""
    from config.telegram import telegram_escape, telegram_xabar_yubor

    reader = berish.oquvchi
    if not reader.telegram_id or Review.objects.filter(book=berish.kitob, reader=reader).exists():
        return
    text = (
        f"📚 <b>{telegram_escape(berish.kitob.nomi)}</b> kitobini qaytardingiz. Kitob sizga yoqdimi?\n"
        "Baho bering — fikringiz boshqa kitobxonlarga kitob tanlashda yordam beradi."
    )
    telegram_xabar_yubor(
        reader.telegram_id, text, organization=berish.organization, reply_markup=rating_keyboard(berish.kitob_id)
    )
