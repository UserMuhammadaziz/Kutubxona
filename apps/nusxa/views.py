from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from berish.serializers import BerishSerializer
from user.permissions import IsLibrarian
from .models import Nusxa
from .serializers import NusxaSerializer, NusxaYaratishSerializer


class NusxaViewSet(viewsets.ModelViewSet):
    """
    GET    /api/copies/       -> ro'yxat (filter: kitob, holati, javon)
    POST   /api/copies/       -> kitobga yangi nusxa qo'shish
    GET    /api/copies/{id}/  -> nusxa kartochkasi + berish tarixi
    PATCH  /api/copies/{id}/  -> holat o'zgartirish (tamirda / yoqolgan / mavjud)
    DELETE /api/copies/{id}/  -> hisobdan chiqarish (faol berishi bo'lmasa)
    """

    permission_classes = [IsLibrarian]
    queryset = Nusxa.objects.select_related("kitob")
    filterset_fields = ["kitob", "holati", "javon"]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.action == "create":
            return NusxaYaratishSerializer
        return NusxaSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = NusxaSerializer(instance).data
        tarix = instance.berish_set.select_related("oquvchi").order_by("-berilgan_sana")
        data["berish_tarixi"] = BerishSerializer(tarix, many=True).data
        return Response(data)

    def perform_destroy(self, instance):
        faol_bor = instance.berish_set.filter(qaytarilgan_sana__isnull=True).exists()
        if faol_bor:
            raise ValidationError(
                {"error": "faol_berish_bor", "detail": "Bu nusxada faol berish bor, o'chirib bo'lmaydi"}
            )
        instance.delete()
