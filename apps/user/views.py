import os

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from organization.models import Membership
from organization.services import check_limit, log_action
from organization.tenancy import joriy_kutubxonani_aniqla, legacy_rejimmi
from .models import User, XatolikXabari
from .permissions import IsAdmin
from .serializers import (
    ParolniAlmashtirishSerializer,
    ProfilniYangilashSerializer,
    UserCreateSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """
    GET   /api/staff/       -> joriy kutubxona xodimlari (faqat administrator)
    POST  /api/staff/       -> yangi kutubxonachi akkaunti yaratish
    GET   /api/staff/{id}/  -> bitta xodim
    PATCH /api/staff/{id}/  -> tahrirlash (masalan is_active=False qilish)
    """

    permission_classes = [IsAdmin]
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        org = joriy_kutubxonani_aniqla(self.request, required=False)
        if org is None:
            if legacy_rejimmi():
                return User.objects.all().order_by("-id")
            return User.objects.none()
        return User.objects.filter(
            a_zoliklar__organization=org, a_zoliklar__faol=True
        ).distinct().order_by("-id")

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "organization": self._org()}

    def _org(self):
        return joriy_kutubxonani_aniqla(self.request, required=False)

    def perform_create(self, serializer):
        org = self._org()
        if org is not None:
            check_limit(
                org,
                "max_staff",
                Membership.objects.filter(organization=org, faol=True).count(),
            )
        user = serializer.save(organization=org)
        log_action(
            "staff.created",
            actor=self.request.user,
            organization=org,
            target_type="user",
            target_id=user.pk,
            metadata={"username": user.username, "rol": user.rol},
            request=self.request,
        )

    def perform_update(self, serializer):
        user = serializer.save()
        org = self._org()
        if org is not None and "rol" in getattr(serializer, "validated_data", {}):
            Membership.objects.filter(organization=org, user=user).update(
                rol=serializer.validated_data["rol"]
            )


class ProfilniYangilashView(APIView):
    """PATCH /api/auth/profile/ — o'z ism-familyasi, logini va telefonini tahrirlash."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        serializer = ProfilniYangilashSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user, context={"request": request}).data)


class XatolikXabariView(APIView):
    """GET/POST /api/auth/xatolik-xabari/ — Profildan xatolik haqida xabar.

    Foydalanuvchi xatolikni qo'lda yozib yuboradi yoki frontend uni avtomatik
    ushlab yuboradi (`tur=avtomatik`). Xabar bazaga saqlanadi va kutubxona
    egasi/administratorlarining Telegram'iga yuboriladi (ID si borlarga).
    Telegram yuborish muvaffaqiyatsiz bo'lsa ham xabar yo'qolmaydi.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        org = joriy_kutubxonani_aniqla(request, required=False)
        sorov = XatolikXabari.objects.select_related("yuborgan")
        if org is not None:
            sorov = sorov.filter(organization=org)
        else:
            # Kutubxona aniqlanmagan legacy rejimda faqat o'zining xabarlarini ko'radi.
            sorov = sorov.filter(yuborgan=request.user)
        natijalar = [
            {
                "id": x.pk,
                "matn": x.matn,
                "sahifa": x.sahifa,
                "tur": x.tur,
                "yaratilgan": x.yaratilgan.isoformat(),
                "yuborgan": (
                    x.yuborgan.get_full_name() or x.yuborgan.username
                    if x.yuborgan
                    else "—"
                ),
            }
            for x in sorov[:10]
        ]
        return Response(natijalar)

    def post(self, request):
        matn = str(request.data.get("matn") or "").strip()
        if not matn:
            raise ValidationError({"matn": "Xatolik tavsifini yozing."})
        sahifa = str(request.data.get("sahifa") or "").strip()[:300]
        tur = request.data.get("tur") or "qolda"
        if tur not in dict(XatolikXabari.TURLARI):
            tur = "qolda"

        org = joriy_kutubxonani_aniqla(request, required=False)
        xabar = XatolikXabari.objects.create(
            organization=org,
            yuborgan=request.user,
            matn=matn[:2000],
            sahifa=sahifa,
            tur=tur,
        )
        yuborildi = self._adminlarga_yubor(xabar, org)
        return Response(
            {
                "id": xabar.pk,
                "saqlandi": True,
                "telegramga_yuborildi": yuborildi,
            },
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _adminlarga_yubor(xabar, org):
        from config.telegram import telegram_escape, telegram_xabar_yubor

        # Fail-closed: kutubxona aniqlanmagan xabarni boshqa barcha tenantlarning
        # administratorlariga tarqatib yubormaymiz.
        if org is None:
            return 0
        sorov = Membership.objects.filter(
            rol__in=["egasi", "administrator"],
            faol=True,
            telegram_id__isnull=False,
            organization=org,
        )

        yuborgan = "—"
        if xabar.yuborgan:
            yuborgan = telegram_escape(
                xabar.yuborgan.get_full_name() or xabar.yuborgan.username
            )
        matn = (
            "⚠️ <b>Tizimda xatolik haqida xabar</b>\n\n"
            f"{telegram_escape(xabar.matn)}\n\n"
            f"Yuborgan: {yuborgan}\n"
            f"Sahifa: {telegram_escape(xabar.sahifa or '—')}\n"
            f"Turi: {'Avtomatik ushlangan' if xabar.tur == 'avtomatik' else 'Qo‘lda yuborilgan'}"
        )
        qabul_qiluvchilar = []
        korilgan = set()
        for azo in sorov.select_related("organization").distinct():
            if azo.telegram_id not in korilgan:
                korilgan.add(azo.telegram_id)
                qabul_qiluvchilar.append((azo.telegram_id, azo.organization))

        # A'zolikda Telegram ID si kiritilmagan o'rnatishlarda xabar yo'qolmasin:
        # .env dagi BOT_ADMIN_CHAT_IDS ham zaxira qabul qiluvchi hisoblanadi.
        for qism in os.environ.get("BOT_ADMIN_CHAT_IDS", "").split(","):
            try:
                chat_id = int(qism.strip())
            except (TypeError, ValueError):
                continue
            if chat_id and chat_id not in korilgan:
                korilgan.add(chat_id)
                qabul_qiluvchilar.append((chat_id, org))

        soni = 0
        for chat_id, qabul_qiluvchi_org in qabul_qiluvchilar:
            if telegram_xabar_yubor(chat_id, matn, organization=qabul_qiluvchi_org):
                soni += 1
        return soni


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except Exception:
                pass
        return Response(status=status.HTTP_205_RESET_CONTENT)


class ParolniAlmashtirishView(APIView):
    """POST /api/auth/change-password/ — o'z parolini almashtirish."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ParolniAlmashtirishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["joriy_parol"]):
            raise ValidationError({"joriy_parol": "Joriy parol noto'g'ri."})
        user.set_password(serializer.validated_data["yangi_parol"])
        user.save(update_fields=["password"])
        return Response({"detail": "Parol muvaffaqiyatli o'zgartirildi."})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    """GET /api/auth/me/ — joriy foydalanuvchi va kutubxonalari."""
    return Response(UserSerializer(request.user, context={"request": request}).data)
