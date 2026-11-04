from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from user.serializers import UserSerializer

from .models import (
    AuditLog,
    Membership,
    Organization,
    OrganizationSubscription,
    SubscriptionPlan,
)
from .permissions import IsPlatformAdmin
from .serializers import (
    MembershipSerializer,
    OrganizationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    SaaSOrganizationSerializer,
)
from .services import check_limit, log_action, set_status, subscription_for
from .tenancy import (
    foydalanuvchi_azoligi,
    foydalanuvchi_kutubxonalari,
    joriy_kutubxonani_aniqla,
)

User = get_user_model()


class RegisterThrottle(AnonRateThrottle):
    scope = "register"
    rate = "10/hour"


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(
            {
                "access": data["access"],
                "refresh": data["refresh"],
                "user": UserSerializer(data["user"]).data,
                "organization": OrganizationSerializer(
                    data["organization"], context={"request": request}
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class OrganizationViewSet(viewsets.GenericViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        return foydalanuvchi_kutubxonalari(self.request.user).order_by("nomi")

    def list(self, request):
        qs = self.get_queryset()
        return Response(
            OrganizationSerializer(qs, many=True, context={"request": request}).data
        )

    def retrieve(self, request, pk=None):
        org = joriy_kutubxonani_aniqla(request, required=True)
        if str(org.pk) != str(pk) and not request.user.is_superuser:
            org = self.get_queryset().filter(pk=pk).first()
        else:
            org = org if str(org.pk) == str(pk) else self.get_queryset().filter(pk=pk).first()
        if not org:
            return Response({"detail": "Kutubxona topilmadi."}, status=404)
        return Response(OrganizationSerializer(org, context={"request": request}).data)

    def partial_update(self, request, pk=None):
        org = self.get_queryset().filter(pk=pk).first()
        if not org:
            return Response({"detail": "Kutubxona topilmadi."}, status=404)
        azolik = foydalanuvchi_azoligi(request.user, org)
        if not request.user.is_superuser and not (azolik and azolik.adminmi):
            return Response({"detail": "Ruxsat yo'q."}, status=403)
        serializer = OrganizationSerializer(
            org, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="telegram-link-code")
    def telegram_link_code(self, request):
        org = joriy_kutubxonani_aniqla(request, required=True)
        azolik = foydalanuvchi_azoligi(request.user, org)
        if not azolik:
            return Response({"detail": "A'zolik topilmadi."}, status=403)
        kod = azolik.yangi_link_kod()
        bot = getattr(org, "telegram_bot", None)
        return Response(
            {
                "code": kod,
                "expires": azolik.link_code_expires,
                "bot_username": bot.username if bot else "",
                "instruksiya": (
                    f"Telegram botga /ulash {kod} yuboring."
                    if bot
                    else "Avval kutubxona Telegram botini ulang."
                ),
            }
        )


class SaaSOrganizationViewSet(viewsets.ModelViewSet):
    """Platforma administratori uchun tashkilotlarni boshqarish API'si."""

    queryset = Organization.objects.select_related("egasi").order_by("-yaratilgan")
    serializer_class = SaaSOrganizationSerializer
    permission_classes = [IsPlatformAdmin]
    http_method_names = ["get", "post", "patch"]
    filterset_fields = ["status", "turi", "faol"]
    search_fields = ["nomi", "slug", "email", "telefon"]

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "request": self.request}

    def _holat(self, request, status, default_reason=""):
        org = self.get_object()
        reason = request.data.get("reason", default_reason)
        set_status(org, status, actor=request.user, reason=reason, request=request)
        return Response(
            SaaSOrganizationSerializer(org, context={"request": request}).data
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._holat(request, Organization.HOLAT_ACTIVE)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._holat(
            request, Organization.HOLAT_REJECTED, "Ariza platforma administratori tomonidan rad etildi."
        )

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        return self._holat(request, Organization.HOLAT_SUSPENDED, "Platforma tomonidan to'xtatilgan.")

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        return self._holat(request, Organization.HOLAT_ACTIVE)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        return self._holat(request, Organization.HOLAT_ARCHIVED, "Arxivlangan.")

    @action(detail=True, methods=["post"], url_path="subscription")
    def subscription(self, request, pk=None):
        """Tarif rejasini o'zgartirish (to'lovsiz, foundation bosqichi)."""
        org = self.get_object()
        obuna = subscription_for(org)
        plan_code = request.data.get("plan")
        if plan_code:
            plan = SubscriptionPlan.objects.filter(code=plan_code, faol=True).first()
            if not plan:
                return Response({"detail": "Tarif rejasi topilmadi."}, status=404)
            obuna.plan = plan
        if "status" in request.data:
            status_value = request.data["status"]
            if status_value not in dict(OrganizationSubscription.HOLAT_CHOICES):
                return Response({"detail": "Obuna holati noto'g'ri."}, status=400)
            obuna.status = status_value
        if "trial_ends_at" in request.data:
            obuna.trial_ends_at = request.data["trial_ends_at"] or None
        if "current_period_end" in request.data:
            obuna.current_period_end = request.data["current_period_end"] or None
        obuna.save()
        log_action(
            "organization.subscription_changed",
            actor=request.user,
            organization=org,
            target_type="organization_subscription",
            target_id=obuna.pk,
            metadata={"plan": obuna.plan.code, "status": obuna.status},
            request=request,
        )
        return Response(
            SaaSOrganizationSerializer(org, context={"request": request}).data
        )

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        from berish.models import Berish
        from kitob.models import Kitob
        from oquvchi.models import Oquvchi

        holatlar = {
            kod: Organization.objects.filter(status=kod).count()
            for kod, _ in Organization.HOLAT_CHOICES
        }
        data = []
        for org in self.get_queryset():
            data.append(
                {
                    "id": org.id,
                    "nomi": org.nomi,
                    "slug": org.slug,
                    "turi": org.turi,
                    "status": org.status,
                    "faol": org.faol,
                    "kitoblar": Kitob.objects.filter(organization=org).count(),
                    "oquvchilar": Oquvchi.objects.filter(organization=org).count(),
                    "berishlar": Berish.objects.filter(organization=org).count(),
                    "azoliklar": Membership.objects.filter(organization=org, faol=True).count(),
                    "bot_ulangan": hasattr(org, "telegram_bot"),
                    "yaratilgan": org.yaratilgan,
                }
            )
        return Response(
            {
                "jami": Organization.objects.count(),
                "holatlar": holatlar,
                "tashkilotlar": data,
            }
        )


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    """Tarif rejalari (o'qish hamma uchun, yozish platforma administratori)."""

    queryset = SubscriptionPlan.objects.all()
    permission_classes = [IsPlatformAdmin]
    http_method_names = ["get", "post", "patch"]

    def get_serializer_class(self):
        from .serializers import SubscriptionPlanSerializer

        return SubscriptionPlanSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Platforma audit jurnali."""

    queryset = AuditLog.objects.select_related("organization", "actor")
    permission_classes = [IsPlatformAdmin]
    filterset_fields = ["organization", "action"]
    search_fields = ["action", "target_type", "target_id"]

    def get_serializer_class(self):
        from .serializers import AuditLogSerializer

        return AuditLogSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user and user.email:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend = getattr(settings, "FRONTEND_URL", "").rstrip("/")
        link = f"{frontend}/parolni-tiklash?uid={uid}&token={token}" if frontend else ""
        xabar = (
            "Parolni tiklash uchun havola:\n"
            f"{link}\n\nAgar bu so'rov sizdan bo'lmasa, xabarni e'tiborsiz qoldiring."
            if link
            else f"Parolni tiklash kodi: uid={uid}&token={token}"
        )
        send_mail(
            "Parolni tiklash",
            xabar,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
    return Response({"detail": "Agar email mavjud bo'lsa, havola yuborildi."})


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        uid = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
        user = User.objects.get(pk=uid, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({"detail": "Havola yaroqsiz."}, status=400)
    if not default_token_generator.check_token(user, serializer.validated_data["token"]):
        return Response({"detail": "Havola eskirgan yoki yaroqsiz."}, status=400)
    user.set_password(serializer.validated_data["password"])
    user.save(update_fields=["password"])
    return Response({"detail": "Parol yangilandi."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_organization(request):
    # Pending/suspended tashkilot egasi ham o'z arizasi holatini ko'rishi
    # kerak — shuning uchun bu endpoint holatni tekshirmaydi.
    org = joriy_kutubxonani_aniqla(request, required=False, allow_inactive=True)
    if not org:
        return Response(None)
    return Response(OrganizationSerializer(org, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_memberships(request):
    qs = Membership.objects.filter(user=request.user, faol=True).select_related(
        "organization"
    )
    data = []
    for azolik in qs:
        item = MembershipSerializer(azolik).data
        item["organization_status"] = azolik.organization.status
        item["organization_status_display"] = azolik.organization.get_status_display()
        data.append(item)
    return Response(data)
