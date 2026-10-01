from django.db import transaction
from django.utils.timezone import now
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from oquvchi.models import Oquvchi
from user.permissions import IsLibrarian
from . import services
from .models import Navbat
from .serializers import (
    NavbatSerializer,
    NavbatYaratishSerializer,
    NavbatJavobSerializer,
    NavbatMeniSerializer,
)


class NavbatViewSet(viewsets.ModelViewSet):
    """
    POST   /api/reservations/               -> navbatga turish (o'quvchi/bot), javobda o'rin qaytadi
    GET    /api/reservations/                -> ro'yxat (kutubxonachi hisoboti)
    GET    /api/reservations/my/            -> o'quvchining navbatlari va o'rni
    POST   /api/reservations/{id}/respond/  -> {"javob": "olaman" | "kerak_emas"}
    POST   /api/reservations/{id}/confirm/  -> kutubxonachi: kitob berildi, navbat yakunlandi
    DELETE /api/reservations/{id}/          -> navbatdan chiqish
    """

    queryset = Navbat.objects.select_related("kitob", "oquvchi")
    serializer_class = NavbatSerializer
    filterset_fields = ["holati", "kitob", "oquvchi"]
    http_method_names = ["get", "post", "delete"]

    def get_permissions(self):
        if self.action in ("create", "meni", "respond", "destroy"):
            return []
        return [IsLibrarian()]

    def create(self, request, *args, **kwargs):
        serializer = NavbatYaratishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        navbat = Navbat.objects.create(
            kitob=serializer.validated_data["kitob"],
            oquvchi=serializer.validated_data["oquvchi"],
        )
        orin = Navbat.objects.filter(
            kitob=navbat.kitob,
            holati="kutmoqda",
            navbat_sanasi__lte=navbat.navbat_sanasi,
        ).count()
        return Response({"id": navbat.id, "orin": orin}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="my")
    def meni(self, request):
        telegram_id = request.query_params.get("telegram_id")
        oquvchi = Oquvchi.objects.filter(telegram_id=telegram_id).first()
        if not oquvchi:
            return Response(
                {"error": "topilmadi", "detail": "O'quvchi bog'lanmagan"},
                status=status.HTTP_404_NOT_FOUND,
            )
        qs = self.queryset.filter(oquvchi=oquvchi, holati__in=["kutmoqda", "taklif_qilindi"])
        return Response(NavbatMeniSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="respond")
    def respond(self, request, pk=None):
        navbat = self.get_object()

        serializer = NavbatJavobSerializer(instance=navbat, data=request.data)
        serializer.is_valid(raise_exception=True)

        # Muddati o'tgan bo'lsa va o'quvchi hali "olaman" demagan bo'lsa,
        # taklif keyingi navbatdagiga o'tadi.
        if navbat.taklif_muddati and now() > navbat.taklif_muddati:
            services.taklifni_bekor_qil_va_keyingisiga_ut(navbat, "muddat_otdi")
            raise ValidationError(
                {"error": "muddat_tugagan", "detail": "Afsus, javob muddati tugagan"}
            )

        javob = serializer.validated_data["javob"]
        with transaction.atomic():
            navbat.javob = javob
            navbat.javob_vaqti = now()
            navbat.save(update_fields=["javob", "javob_vaqti"])
            if javob == "kerak_emas":
                services.taklifni_bekor_qil_va_keyingisiga_ut(navbat, "oquvchi_rad")

        navbat.refresh_from_db()
        return Response(NavbatSerializer(navbat).data)

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        """Kutubxonachi kitobni o'quvchiga berdi — navbat 'yakunlandi' deb
        belgilanadi va ajratilgan nusxa bo'shatiladi (aks holda u 'band'
        holatda qolib, boshqa o'quvchilarga berilmay qolardi)."""
        navbat = self.get_object()
        if navbat.holati not in ("kutmoqda", "taklif_qilindi"):
            raise ValidationError(
                {"error": "holat_notogri", "detail": "Faqat faol navbat tasdiqlanadi"}
            )

        with transaction.atomic():
            nusxa = navbat.ajratilgan_nusxa
            if nusxa and nusxa.holati == "band":
                nusxa.holati = "mavjud"
                nusxa.save(update_fields=["holati"])
            navbat.holati = "yakunlandi"
            navbat.javob_vaqti = now()
            navbat.taklif_xabari_yuborilgan = False
            navbat.save(
                update_fields=["holati", "javob_vaqti", "taklif_xabari_yuborilgan"]
            )
        return Response(NavbatSerializer(navbat).data)

    def destroy(self, request, *args, **kwargs):
        navbat = self.get_object()
        with transaction.atomic():
            if navbat.holati == "taklif_qilindi":
                services.taklifni_bekor_qil_va_keyingisiga_ut(
                    navbat, "oquvchi_chiqdi", oquvchi_rozi=True
                )
            else:
                navbat.holati = "bekor"
                navbat.bekor_sababi = "oquvchi_chiqdi"
                navbat.save(update_fields=["holati", "bekor_sababi"])
        return Response(status=status.HTTP_204_NO_CONTENT)
