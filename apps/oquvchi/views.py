from django.db import transaction
from django.utils.timezone import now
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from berish.serializers import BerishMeniSerializer
from jarima.models import Jarima
from jarima.serializers import JarimaMeniSerializer
from user.permissions import IsLibrarian
from .models import Ariza, Oquvchi
from .serializers import (
    ArizaSerializer,
    ArizaStatusSerializer,
    ArizaYaratishSerializer,
    OquvchiSerializer,
    OquvchiYaratishSerializer,
    OquvchiBindSerializer,
    _yangi_karta_raqami,
)


class OquvchiViewSet(viewsets.ModelViewSet):
    """
    GET   /api/readers/       -> ro'yxat (qidiruv: fish, telefon, karta_raqami)
    POST  /api/readers/       -> yangi o'quvchi ro'yxatga olish (karta_raqami avtomatik)
    GET   /api/readers/{id}/  -> o'quvchi kartochkasi: joriy kitoblari va jarimalari
    PATCH /api/readers/{id}/  -> tahrirlash
    POST  /api/readers/bind/  -> bot: telefon + karta_raqami bo'yicha telegram_id ni bog'lash
    """

    permission_classes = [IsLibrarian]
    queryset = Oquvchi.objects.all().order_by("-royxat_sanasi", "-id")
    search_fields = ["fish", "telefon", "karta_raqami"]
    http_method_names = ["get", "post", "patch"]

    def get_serializer_class(self):
        if self.action == "create":
            return OquvchiYaratishSerializer
        return OquvchiSerializer

    def get_permissions(self):
        if self.action == "bind":
            return []
        return [IsLibrarian()]

    def retrieve(self, request, *args, **kwargs):
        oquvchi = self.get_object()
        data = OquvchiSerializer(oquvchi).data

        joriy = oquvchi.berish_set.filter(qaytarilgan_sana__isnull=True)
        data["joriy_kitoblari"] = BerishMeniSerializer(joriy, many=True).data

        jarimalar = Jarima.objects.filter(berish__oquvchi=oquvchi, tolandimi=False)
        data["jarimalari"] = JarimaMeniSerializer(jarimalar, many=True).data

        return Response(data)

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
    filterset_fields = ["holati"]
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

        with transaction.atomic():
            oquvchi = Oquvchi.objects.filter(telefon=ariza.telefon).first()
            if oquvchi:
                oquvchi.telegram_id = ariza.telegram_id
                oquvchi.fish = ariza.fish
                oquvchi.faol = True
                yangilash = ["telegram_id", "fish", "faol"]
                if ariza.tugilgan_sana:
                    oquvchi.tugilgan_sana = ariza.tugilgan_sana
                    yangilash.append("tugilgan_sana")
                if ariza.manzil:
                    oquvchi.manzil = ariza.manzil
                    yangilash.append("manzil")
                oquvchi.save(update_fields=yangilash)
            else:
                oquvchi = Oquvchi.objects.create(
                    fish=ariza.fish,
                    telefon=ariza.telefon,
                    telegram_id=ariza.telegram_id,
                    karta_raqami=_yangi_karta_raqami(),
                    tugilgan_sana=ariza.tugilgan_sana,
                    manzil=ariza.manzil,
                )
            ariza.holati = "tasdiqlandi"
            ariza.tasdiqlangan_sana = now()
            ariza.save(update_fields=["holati", "tasdiqlangan_sana"])

        return Response(ArizaSerializer(ariza).data)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        ariza = self.get_object()
        if ariza.holati != "kutmoqda":
            raise ValidationError(
                {"error": "holat_notogri", "detail": "Faqat 'kutmoqda' holatidagi ariza rad etiladi"}
            )
        ariza.holati = "bekor"
        ariza.izoh = request.data.get("izoh", "")[:255]
        ariza.save(update_fields=["holati", "izoh"])
        return Response(ArizaSerializer(ariza).data)
