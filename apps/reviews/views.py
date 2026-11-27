from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from kitob.models import Kitob
from oquvchi.models import Oquvchi
from organization.tenancy import joriy_kutubxonani_aniqla, scope
from telegrambot.views import IsBotService, _polling_bot_organization
from user.permissions import IsLibrarian

from . import services
from .models import Review


def _review(review, *, staff=False):
    data = {
        "id": review.id,
        "book": review.book_id,
        "rating": review.rating,
        "text": review.text,
        "author": services.reader_label(review.reader),
        "updated_at": review.updated_at,
    }
    if staff:
        data.update(reader=review.reader_id, reader_name=review.reader.fish, is_hidden=review.is_hidden)
    return data


class ReviewListView(APIView):
    """GET /api/reviews/?book=<id> — every review of a book, hidden ones too (librarians)."""

    permission_classes = [IsLibrarian]

    def get(self, request):
        org = joriy_kutubxonani_aniqla(request)
        book = scope(Kitob.objects, org).filter(pk=request.query_params.get("book") or 0).first()
        if book is None:
            return Response({"error": "not_found", "detail": "Kitob topilmadi."}, status=404)
        reviews = scope(Review.objects, org).filter(book=book).select_related("reader")
        return Response(
            {"summary": services.summary(book), "results": [_review(r, staff=True) for r in reviews]}
        )


class ReviewHideView(APIView):
    """POST /api/reviews/<id>/hide/ {"hidden": true|false}."""

    permission_classes = [IsLibrarian]

    def post(self, request, pk):
        org = joriy_kutubxonani_aniqla(request)
        review = scope(Review.objects, org).select_related("reader").filter(pk=pk).first()
        if review is None:
            return Response({"error": "not_found", "detail": "Fikr topilmadi."}, status=404)
        review.is_hidden = bool(request.data.get("hidden", True))
        review.save(update_fields=["is_hidden", "updated_at"])
        return Response(_review(review, staff=True))


class BotReviewView(APIView):
    """The polling bot: read a book's reviews and save the reader's own.

    GET  ?book=&telegram_id=  → summary, latest reviews, can_review, mine
    POST {book, telegram_id, rating, text}
    """

    permission_classes = [IsBotService]

    def _context(self, request, source):
        org = _polling_bot_organization(request)
        if org is None:
            return None, None, Response({"detail": "Bot kutubxonaga ulanmagan."}, status=400)
        book = scope(Kitob.objects, org).filter(pk=str(source.get("book") or "0").strip() or 0).first()
        if book is None:
            return None, None, Response({"detail": "Kitob topilmadi."}, status=404)
        reader = scope(Oquvchi.objects, org).filter(telegram_id=source.get("telegram_id") or 0).first()
        return book, reader, None

    def get(self, request):
        book, reader, error = self._context(request, request.query_params)
        if error:
            return error
        mine = Review.objects.filter(book=book, reader=reader).first() if reader else None
        return Response(
            {
                "book_title": book.nomi,
                "summary": services.summary(book),
                "reviews": [_review(r) for r in services.public_reviews(book)],
                "can_review": bool(reader and services.has_read(reader, book)),
                "mine": {"rating": mine.rating, "text": mine.text} if mine else None,
            }
        )

    def post(self, request):
        book, reader, error = self._context(request, request.data)
        if error:
            return error
        if reader is None:
            return Response({"detail": "Avval kutubxona kartangizni bog'lang (/start)."}, status=403)
        if not services.has_read(reader, book):
            return Response({"detail": "Fikrni kitobni o'qib, qaytargandan keyin qoldirish mumkin."}, status=403)
        try:
            review = services.save_review(reader, book, request.data.get("rating"), request.data.get("text", ""))
        except (TypeError, ValueError):
            return Response({"detail": "Baho 1 dan 5 gacha bo'lishi kerak."}, status=400)
        return Response(_review(review), status=status.HTTP_201_CREATED)
