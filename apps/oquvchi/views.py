from datetime import date

from django.db import transaction
from django.db.models import F, Sum
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from berish.models import Berish
from berish.serializers import BerishMeniSerializer
from config.telegram import telegram_escape
from telegrambot.services import organizatsiya_xabari
from jarima.models import Jarima
from jarima.serializers import JarimaMeniSerializer
from user.permissions import IsLibrarian
from . import services
from .filters import ReaderFilter
from .models import Ariza, Fan, Oquvchi
from .serializers import (
    ArizaSerializer,
    ArizaStatusSerializer,
    ArizaYaratishSerializer,
    FanSerializer,
    OquvchiSerializer,
    OquvchiYaratishSerializer,
    OquvchiBindSerializer,
)


def _reader_stats(reader):
    """Aggregate numbers for the reader profile header."""
    today = date.today()
    loans = Berish.objects.filter(oquvchi=reader)
    fines = Jarima.objects.filter(berish__oquvchi=reader)
    unpaid = fines.filter(tolandimi=False).aggregate(s=Sum("summa"))["s"] or 0
    paid = fines.filter(tolandimi=True).aggregate(s=Sum("summa"))["s"] or 0
    return {
        "total_loans": loans.count(),
        "active_loans": loans.filter(qaytarilgan_sana__isnull=True).count(),
        "overdue_loans": loans.filter(
            qaytarilgan_sana__isnull=True, qaytarish_muddati__lt=today
        ).count(),
        "returned_late": loans.filter(
            qaytarilgan_sana__gt=F("qaytarish_muddati")
        ).count(),
        "unpaid_fines_total": unpaid,
        "paid_fines_total": paid,
    }


def _reader_history(reader, limit=30):
    """Latest loans (active and returned), newest first."""
    today = date.today()
    loans = (
        Berish.objects.filter(oquvchi=reader)
        .select_related("kitob", "nusxa")
        .prefetch_related("jarima")
        .order_by("-berilgan_sana", "-id")[:limit]
    )
    rows = []
    for loan in loans:
        returned = loan.qaytarilgan_sana
        if returned:
            status_ = "returned"
        elif loan.qaytarish_muddati < today:
            status_ = "overdue"
        else:
            status_ = "active"
        fine = getattr(loan, "jarima", None)
        rows.append(
            {
                "id": loan.id,
                "book_title": loan.kitob.nomi,
                "issued_at": loan.berilgan_sana,
                "due_date": loan.qaytarish_muddati,
                "returned_at": returned,
                "status": status_,
                "fine_amount": fine.summa if fine else None,
                "fine_paid": fine.tolandimi if fine else None,
            }
        )
    return rows


class OquvchiViewSet(viewsets.ModelViewSet):
    """
    GET   /api/readers/       -> ro'yxat (qidiruv: fish, telefon, karta_raqami)
    GET   /api/readers/?rol=oqituvchi -> faqat o'qituvchilar ("O'qituvchilar" bo'limi)
    POST  /api/readers/       -> yangi o'quvchi ro'yxatga olish (karta_raqami avtomatik)
    GET   /api/readers/{id}/  -> o'quvchi kartochkasi: joriy kitoblari va jarimalari
    PATCH /api/readers/{id}/  -> tahrirlash
    POST  /api/readers/bind/  -> bot: telefon + karta_raqami bo'yicha telegram_id ni bog'lash
    """

    permission_classes = [IsLibrarian]
    queryset = Oquvchi.objects.all().order_by("-royxat_sanasi", "-id")
    search_fields = ["fish", "telefon", "karta_raqami"]
    filterset_class = ReaderFilter
    http_method_names = ["get", "post", "patch"]

    def get_serializer_class(self):
        if self.action == "create":
            return OquvchiYaratishSerializer
        return OquvchiSerializer

    def get_permissions(self):
        # `bind` ochiq emas: telefon + karta raqamini bilgan har kim
        # internet orqali o'quvchi akkauntini o'z telegram_id'siga qayta
        # bog'lashi (akkount egallash) mumkin edi. Endi so'rov
        # autentifikatsiyalangan bo'lishi shart — bot o'z xizmat
        # akkaunti JWT'si bilan chaqiradi.
        return [IsLibrarian()]

    def retrieve(self, request, *args, **kwargs):
        oquvchi = self.get_object()
        data = OquvchiSerializer(oquvchi).data

        joriy = oquvchi.berish_set.filter(qaytarilgan_sana__isnull=True)
        data["joriy_kitoblari"] = BerishMeniSerializer(joriy, many=True).data

        jarimalar = Jarima.objects.filter(berish__oquvchi=oquvchi, tolandimi=False)
        data["jarimalari"] = JarimaMeniSerializer(jarimalar, many=True).data

        # New English keys (profile page): statistics + loan history.
        data["stats"] = _reader_stats(oquvchi)
        data["history"] = _reader_history(oquvchi)

        return Response(data)

    @action(detail=True, methods=["post"], url_path="message")
    def message(self, request, pk=None):
        """POST /api/readers/{id}/message/ {"text": "..."} -> Telegram message to this reader."""
        reader = self.get_object()
        text = str(request.data.get("text", "")).strip()
        if not text:
            raise ValidationError({"text": "Xabar matni bo‘sh bo‘lmasligi kerak."})
        if len(text) > 1000:
            raise ValidationError({"text": "Xabar 1000 belgidan oshmasligi kerak."})
        if not reader.telegram_id:
            raise ValidationError({"detail": "O‘quvchi Telegram botga ulanmagan."})
        sent = organizatsiya_xabari(reader.organization, reader.telegram_id, telegram_escape(text))
        if not sent:
            raise ValidationError({"detail": "Xabar yuborilmadi. Bot ulanganini tekshiring."})
        return Response({"sent": True})

    @action(detail=False, methods=["post"], url_path="bind")
    def bind(self, request):
        serializer = OquvchiBindSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        oquvchi = serializer.save()
        return Response(OquvchiSerializer(oquvchi).data, status=status.HTTP_200_OK)


class ArizaViewSet(viewsets.ModelViewSet):
    """
    POST   /api/applications/            -> yangi a'zolik arizasi (bot, ochiq)
    GET    /api/applications/            -> arizalar ro'yxati (kutubxonachi)
    GET    /api/applications/status/?telegram_id= -> ariza holati (bot, ochiq)
    POST   /api/applications/{id}/approve/ -> tasdiqlash: Oquvchi yaratib, telegram_id bog'laydi
    POST   /api/applications/{id}/reject/ -> rad etish
    """

    queryset = Ariza.objects.all()
    serializer_class = ArizaSerializer
    filterset_fields = ["holati", "sinf", "rol"]
    search_fields = ["fish", "telefon", "telegram_id", "kasb"]
    http_method_names = ["get", "post"]

    def get_permissions(self):
        if self.action in ("create", "holat"):
            return []
        return [IsLibrarian()]

    def get_serializer_class(self):
        if self.action == "create":
            return ArizaYaratishSerializer
        return ArizaSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ariza = serializer.save()
        return Response(ArizaSerializer(ariza).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="status")
    def holat(self, request):
        telegram_id = request.query_params.get("telegram_id")
        if not telegram_id:
            raise ValidationError(
                {"error": "telegram_id_kerak", "detail": "telegram_id parametri kiritilishi shart"}
            )
        ariza = Ariza.objects.filter(telegram_id=telegram_id).first()
        if ariza:
            data = {
                "holati": ariza.holati,
                "izoh": ariza.izoh or "",
            }
        else:
            data = {"holati": None, "izoh": ""}
        serializer = ArizaStatusSerializer(data)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        ariza = self.get_object()
        if ariza.holati != "kutmoqda":
            raise ValidationError(
                {"error": "holat_notogri", "detail": "Faqat 'kutmoqda' holatidagi ariza tasdiqlanadi"}
            )
        if Oquvchi.objects.filter(telegram_id=ariza.telegram_id).exists():
            raise ValidationError(
                {"error": "telegram_band", "detail": "Bu telegram akkaunt allaqachon o'quvchiga bog'langan"}
            )

        try:
            with transaction.atomic():
                ariza, oquvchi, yangi_karta = services.arizani_tasdiqla(ariza)
                services.ariza_holatini_yubor(
                    ariza, services.tasdiqlash_xabari(ariza, oquvchi, yangi_karta)
                )
        except services.ArizaTelegramBandi as xato:
            raise ValidationError({"error": "telefon_band", "detail": str(xato)})

        return Response(ArizaSerializer(ariza).data)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        ariza = self.get_object()
        if ariza.holati != "kutmoqda":
            raise ValidationError(
                {"error": "holat_notogri", "detail": "Faqat 'kutmoqda' holatidagi ariza rad etiladi"}
            )

        with transaction.atomic():
            services.arizani_rad_et(ariza, request.data.get("izoh", ""))
            services.ariza_holatini_yubor(ariza, services.rad_etilgan_xabari(ariza, ariza.izoh))

        return Response(ArizaSerializer(ariza).data)


class FanViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/subjects/ — o'qituvchi ariza berayotganda tanlaydigan fanlar ro'yxati."""

    serializer_class = FanSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    queryset = Fan.objects.filter(faol=True)
