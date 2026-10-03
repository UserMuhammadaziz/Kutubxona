from django.db.models import Count, Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from navbat.serializers import NavbatSerializer
from user.permissions import IsLibrarian
from .models import BandQilish, Kitob
from .serializers import (
    BandQilishMeniSerializer,
    BandQilishSerializer,
    BandQilishTasdiqSerializer,
    BandQilishYaratishSerializer,
    KitobSerializer,
    KitobDetailSerializer,
    KitobQidiruvSerializer,
)
from . import services

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
        if self.action in ("create", "partial_update", "update", "destroy", "hold"):
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
        # Nusxa, Berish va Navbat `kitob` maydoni PROTECT/CASCADE bilan
        # bog'langan: shu sababli faol berish yoki navbat bor kitobni
        # o'chirish `ProtectedError` berib, 500 qaytarardi. Oldindan
        # tekshirib, foydalanuvchiga tushunarli xato qaytaramiz.
        if instance.nusxalar.exists():
            raise ValidationError(
                {"error": "nusxa_mavjud", "detail": "Kitobda hali nusxalar bor, o'chirib bo'lmaydi"}
            )

        faol_berishlar = instance.berishlar.filter(qaytarilgan_sana__isnull=True)
        if faol_berishlar.exists():
            raise ValidationError(
                {
                    "error": "faol_berish_mavjud",
                    "detail": (
                        "Kitob hali o'quvchilarda qaytarilmagan. Avval "
                        "qaytarilishini to'g'rilang, keyin o'chiring."
                    ),
                }
            )

        faol_navbat = instance.navbat.filter(holati__in=NAVBAT_FAQOL)
        if faol_navbat.exists():
            raise ValidationError(
                {
                    "error": "navbat_mavjud",
                    "detail": "Kitob uchun faol navbat bor, avval navbatni tozalang.",
                }
            )

        # Berish tarihi PROTECT — o'quvchilarda qaytarilgan, lekin tarixi
        # bor kitobni o'chirish ham ma'lumot butunligini buzadi. Bu yerda
        # aniq xabar beramiz (aks holda Django "500" qaytarardi).
        if instance.berishlar.exists():
            raise ValidationError(
                {
                    "error": "berish_tarixi_mavjud",
                    "detail": "Kitobning berish tarihi bor, uni o'chirib bo'lmaydi.",
                }
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

    @action(detail=True, methods=["get"], permission_classes=[IsLibrarian])
    def hold(self, request, pk=None):
        """GET /api/books/{id}/hold/ — shu kitobning kutilayotgan band so'rovi."""
        band = services.faol_bandni_top(pk)
        return Response(BandQilishSerializer(band).data if band else None)


class BandQilishViewSet(viewsets.ViewSet):
    """Kitobni band qilish (saqlab qo'yish) so'rovlari.

    POST   /api/holds/                 -> band qilish so'rovi (bot yoki panel)
    GET    /api/holds/                 -> ro'yxat (kutubxonachi hisoboti)
    GET    /api/holds/my/              -> o'quvchining o'z so'rovlari
    POST   /api/holds/{id}/approve/    -> tasdiqlash: kitobni so'rovchiga berish
    POST   /api/holds/{id}/reject/     -> rad etish
    POST   /api/holds/{id}/cancel/     -> o'quvchi o'z so'rovini bekor qiladi
    """

    queryset = BandQilish.objects.select_related(
        "kitob", "oquvchi", "tasdiqlovchi", "berish"
    )
    serializer_class = BandQilishSerializer
    http_method_names = ["get", "post"]

    def get_permissions(self):
        # So'rov yaratish va bekor qilish bot (xizmat akkaunti) ham,
        # o'quvchi ham ishlatadi; tasdiqlash/rad etish va hisobot — faqat
        # kutubxonachi yoki administrator.
        if self.action in ("create", "meni", "cancel"):
            return [permissions.IsAuthenticated()]
        return [IsLibrarian()]

    def get_queryset(self):
        qs = self.queryset
        holati = self.request.query_params.get("holati")
        if holati:
            qs = qs.filter(holati=holati)
        kitob = self.request.query_params.get("kitob")
        if kitob:
            qs = qs.filter(kitob_id=kitob)
        return qs

    def list(self, request):
        qs = self.get_queryset()
        return Response(BandQilishSerializer(qs, many=True).data)

    def create(self, request):
        """Kitobni band qilish so'rovi (kitob id URL da)."""
        kitob_id = request.data.get("kitob")
        if not kitob_id:
            raise ValidationError(
                {"error": "kitob_kerak", "detail": "kitob (id) kiritilishi shart"}
            )
        kitob = Kitob.objects.filter(pk=kitob_id).first()
        if not kitob:
            return Response(
                {"error": "kitob_topilmadi", "detail": "Kitob topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BandQilishYaratishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        oquvchi = serializer.validated_data["oquvchi"]

        band, yangi = services.band_qilish(
            kitob, oquvchi, serializer.validated_data.get("izoh", "")
        )
        band = self.queryset.get(pk=band.pk)
        return Response(
            BandQilishSerializer(band).data,
            status=status.HTTP_201_CREATED if yangi else status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="my")
    def meni(self, request):
        from oquvchi.models import Oquvchi

        telegram_id = request.query_params.get("telegram_id")
        oquvchi = Oquvchi.objects.filter(telegram_id=telegram_id).first()
        if not oquvchi:
            return Response(
                {"error": "topilmadi", "detail": "O'quvchi bog'lanmagan"},
                status=status.HTTP_404_NOT_FOUND,
            )
        qs = self.queryset.filter(oquvchi=oquvchi)[:50]
        return Response(BandQilishMeniSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Tasdiqlash: kitob so'rov qilgan o'quvchiga beriladi."""
        band = self._band(pk)
        services.band_qilishni_tasdiqla(
            band, request.user, request.data.get("izoh", "")
        )
        return Response(BandQilishSerializer(self.queryset.get(pk=band.pk)).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Rad etish: kitob banddan chiqadi va yana berishga ochiq bo'ladi."""
        band = self._band(pk)
        services.band_qilishni_rad_et(band, request.user, request.data.get("izoh", ""))
        return Response(BandQilishSerializer(self.queryset.get(pk=band.pk)).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """O'quvchi o'z kutilayotgan so'rovini bekor qiladi."""
        from oquvchi.models import Oquvchi

        band = self._band(pk)
        telegram_id = request.data.get("telegram_id")
        oquvchi = Oquvchi.objects.filter(telegram_id=telegram_id).first()
        if not oquvchi:
            return Response(
                {"error": "topilmadi", "detail": "O'quvchi bog'lanmagan"},
                status=status.HTTP_404_NOT_FOUND,
            )
        services.band_qilishni_bekor_qil(band, oquvchi)
        return Response(BandQilishSerializer(self.queryset.get(pk=band.pk)).data)

    def _band(self, pk):
        band = self.queryset.filter(pk=pk).first()
        if not band:
            raise ValidationError({"error": "topilmadi", "detail": "So'rov topilmadi"})
        return band






