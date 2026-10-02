from django.utils.timezone import now
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from oquvchi.models import Oquvchi
from user.permissions import IsLibrarian
from . import services
from berish.models import Berish
from berish.serializers import BerishSerializer, BerishYaratishSerializer, BerishMeniSerializer


class BerishViewSet(viewsets.ModelViewSet):
    permission_classes = [IsLibrarian]
    queryset = Berish.objects.select_related("nusxa", "kitob", "oquvchi").order_by("-id")
    serializer_class = BerishSerializer
    filterset_fields = ["holati", "oquvchi"]
    http_method_names = ["get", "post"]

    def get_permissions(self):
        if self.action == "meni":
            return []
        return [IsLibrarian()]

    def create(self, request, *args, **kwargs):
        serializer = BerishYaratishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        malumot = serializer.validated_data
        if malumot.get("kitob"):
            berish = services.kitob_ber_by_kitob(
                kitob=malumot["kitob"],
                oquvchi=malumot["oquvchi"],
                xodim=request.user,
            )
        else:
            berish = services.kitob_ber(
                nusxa=malumot["nusxa"],
                oquvchi=malumot["oquvchi"],
                xodim=request.user,
            )
        return Response(BerishSerializer(berish).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="return")
    def qaytarish(self, request, pk=None):
        berish = self.get_object()
        berish, jarima, taklif_ketdi = services.kitob_qaytar(berish, request.user)
        return Response(
            {
                "berish": BerishSerializer(berish).data,
                "jarima_summasi": jarima.summa if jarima else None,
                "navbatga_taklif_ketdimi": taklif_ketdi,
            }
        )

    @action(detail=False, methods=["get"], url_path="my")
    def meni(self, request):
        telegram_id = request.query_params.get("telegram_id")
        oquvchi = Oquvchi.objects.filter(telegram_id=telegram_id).first()
        if not oquvchi:
            return Response(
                {"error": "topilmadi", "detail": "O'quvchi bog'lanmagan"},
                status=status.HTTP_404_NOT_FOUND,
            )
        qs = self.queryset.filter(oquvchi=oquvchi, qaytarilgan_sana__isnull=True)
        return Response(BerishMeniSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="overdue")
    def overdue(self, request):
        qs = self.queryset.filter(qaytarilgan_sana__isnull=True, qaytarish_muddati__lt=now().date())
        return Response(BerishSerializer(qs, many=True).data)
