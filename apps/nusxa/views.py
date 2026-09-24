from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from berish.serializers import BerishSerializer
from user.permissions import IsLibrarian
from .models import Nusxa
from .serializers import NusxaSerializer, NusxaYaratishSerializer


class NusxaViewSet(viewsets.ModelViewSet):
    """
    GET    /api/copies/
    POST   /api/copies/
    GET    /api/copies/{id}/
    PATCH  /api/copies/{id}/
    DELETE /api/copies/{id}/
    """

    permission_classes = [IsLibrarian]
    queryset = Nusxa.objects.select_related("kitob").order_by("-qabul_sana", "-id")
    filterset_fields = ["kitob", "holati", "javon", "inventar_raqami"]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.action == "create":
            return NusxaYaratishSerializer

        return NusxaSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        data = NusxaSerializer(instance).data

        tarix = (
            instance.berish_set
            .select_related("oquvchi")
            .order_by("-berilgan_sana")
        )

        data["berish_tarixi"] = BerishSerializer(
            tarix,
            many=True
        ).data

        return Response(data)

    def perform_destroy(self, instance):
        # Faol berish bor-yo'qligini tekshiramiz
        faol_bor = instance.berish_set.filter(
            qaytarilgan_sana__isnull=True
        ).exists()

        if faol_bor:
            raise ValidationError({
                "error": "faol_berish_bor",
                "detail": "Bu nusxa hozir o'quvchiga berilgan. Uni o'chirib bo'lmaydi."
            })

        # Eski berish tarixi mavjud bo'lsa,
        # ForeignKey(PROTECT) sababli fizik DELETE qilish mumkin emas.
        tarix_bor = instance.berish_set.exists()

        if tarix_bor:
            raise ValidationError({
                "error": "berish_tarixi_bor",
                "detail": (
                    "Bu nusxaning berish tarixi mavjud. "
                    "Tarixni saqlash uchun nusxani fizik o'chirish mumkin emas. "
                    "Nusxani 'Yo'qolgan' yoki 'Ta'mirda' holatiga o'tkazing."
                )
            })

        # Hech qanday tarix bo'lmasa, o'chiramiz
        instance.delete()