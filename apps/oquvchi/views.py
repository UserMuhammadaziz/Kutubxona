from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from berish.serializers import BerishMeniSerializer
from jarima.models import Jarima
from jarima.serializers import JarimaMeniSerializer
from user.permissions import IsLibrarian
from .models import Oquvchi
from .serializers import OquvchiSerializer, OquvchiYaratishSerializer, OquvchiBindSerializer


class OquvchiViewSet(viewsets.ModelViewSet):
    """
    GET   /api/readers/       -> ro'yxat (qidiruv: fish, telefon, karta_raqami)
    POST  /api/readers/       -> yangi o'quvchi ro'yxatga olish (karta_raqami avtomatik)
    GET   /api/readers/{id}/  -> o'quvchi kartochkasi: joriy kitoblari va jarimalari
    PATCH /api/readers/{id}/  -> tahrirlash
    POST  /api/readers/bind/  -> bot: telefon + karta_raqami bo'yicha telegram_id ni bog'lash
    """

    permission_classes = [IsLibrarian]
    queryset = Oquvchi.objects.all()
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
