from django.utils.timezone import now
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from oquvchi.models import Oquvchi
from user.permissions import IsLibrarian
from .models import Jarima
from .serializers import JarimaSerializer, JarimaTolashSerializer, JarimaMeniSerializer


class JarimaViewSet(viewsets.ModelViewSet):
    """
    GET  /api/fines/          -> ro'yxat (filter: tolandimi, oquvchi)
    GET  /api/fines/my/       -> o'quvchining to'lanmagan jarimalari va umumiy qarzi
    POST /api/fines/{id}/pay/ -> jarimani to'langan deb belgilash
    """

    queryset = Jarima.objects.select_related("berish__oquvchi", "berish__nusxa__kitob")
    serializer_class = JarimaSerializer
    filterset_fields = ["tolandimi", "berish__oquvchi"]
    http_method_names = ["get", "post"]

    def get_permissions(self):
        if self.action == "meni":
            return []
        return [IsLibrarian()]

    @action(detail=False, methods=["get"], url_path="my")
    def meni(self, request):
        telegram_id = request.query_params.get("telegram_id")
        oquvchi = Oquvchi.objects.filter(telegram_id=telegram_id).first()
        if not oquvchi:
            return Response(
                {"error": "topilmadi", "detail": "O'quvchi bog'lanmagan"},
                status=status.HTTP_404_NOT_FOUND,
            )
        qs = self.queryset.filter(berish__oquvchi=oquvchi, tolandimi=False)
        umumiy = sum(jarima.summa for jarima in qs)
        return Response(
            {
                "jarimalar": JarimaMeniSerializer(qs, many=True).data,
                "umumiy_qarz": umumiy,
            }
        )

    @action(detail=True, methods=["post"], url_path="pay")
    def pay(self, request, pk=None):
        jarima = self.get_object()
        serializer = JarimaTolashSerializer(instance=jarima, data={})
        serializer.is_valid(raise_exception=True)

        jarima.tolandimi = True
        jarima.tolangan_sana = now()
        jarima.qabul_qilgan = request.user
        jarima.save(update_fields=["tolandimi", "tolangan_sana", "qabul_qilgan"])
        return Response(JarimaSerializer(jarima).data)
