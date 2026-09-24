from django.db.models import Count, Q
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from navbat.serializers import NavbatSerializer
from user.permissions import IsLibrarian
from .models import Kitob
from .serializers import KitobSerializer, KitobDetailSerializer, KitobQidiruvSerializer

# Faol (bekor qilinmagan / yakunlanmagan) navbat holatlari.
NAVBAT_FAQOL = ("kutmoqda", "taklif_qilindi")


class KitobViewSet(viewsets.ModelViewSet):
    queryset = Kitob.objects.all().order_by("nomi")
    filterset_fields = ["janr", "muallif", "nashr_yili"]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return KitobDetailSerializer
        if self.action == "list":
            # ro'yxatda mavjud/jami nusxalar sonini ko'rsatish uchun annotate qilingan serializer
            return KitobQidiruvSerializer
        return KitobSerializer

    def get_permissions(self):
        if self.action in ("create", "partial_update", "update", "destroy"):
            return [IsLibrarian()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if self.action in ("retrieve",):
            return Kitob.objects.prefetch_related("nusxalar")
        if self.action == "list":
            return (
                Kitob.objects.all()
                .order_by("nomi")
                .annotate(
                    mavjud_nusxalar=Count("nusxalar", filter=Q(nusxalar__holati="mavjud")),
                    jami_nusxalar=Count("nusxalar"),
                    faol_navbatlar=Count("navbat", filter=Q(navbat__holati__in=NAVBAT_FAQOL)),
                )
            )
        return super().get_queryset()

    def perform_destroy(self, instance):
        if instance.nusxalar.exists():
            raise ValidationError(
                {"error": "nusxa_mavjud", "detail": "Kitobda hali nusxalar bor, o'chirib bo'lmaydi"}
            )
        instance.delete()

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        q = request.query_params.get("q", "")
        qs = Kitob.objects.filter(
            Q(nomi__icontains=q) | Q(muallif__icontains=q) | Q(isbn__icontains=q)
        ).annotate(
            mavjud_nusxalar=Count("nusxalar", filter=Q(nusxalar__holati="mavjud")),
            jami_nusxalar=Count("nusxalar"),
            faol_navbatlar=Count("navbat", filter=Q(navbat__holati__in=NAVBAT_FAQOL)),
        )
        serializer = KitobQidiruvSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="genres")
    def genres(self, request):
        """Bot uchun: mavjud kitoblari bor janrlar ro'yxati."""
        labels = dict(Kitob.JANR_CHOICES)
        qs = (
            Kitob.objects.values("janr")
            .annotate(soni=Count("id"))
            .order_by("janr")
        )
        data = [
            {"key": r["janr"], "label": labels.get(r["janr"], r["janr"]), "soni": r["soni"]}
            for r in qs
        ]
        return Response(data)

    @action(detail=True, methods=["get"], url_path="queue", permission_classes=[IsLibrarian])
    def queue(self, request, pk=None):
        kitob = self.get_object()
        qs = kitob.navbat.filter(holati__in=["kutmoqda", "taklif_qilindi"]).order_by("navbat_sanasi")
        serializer = NavbatSerializer(qs, many=True)
        return Response(serializer.data)






