from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status, viewsets
from rest_framework.parsers import MultiPartParser
from .logo import LogoError, remove_old_logos, save_logo
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from user.serializers import UserSerializer

from .models import (
    AuditLog,
    Membership,
    Organization,
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
    SubscriptionChangeSerializer,
)
from .services import DEFAULT_PLAN_CODE, log_action, set_status, subscription_for
from .tenancy import (
    foydalanuvchi_azoligi,
    foydalanuvchi_kutubxonalari,
    joriy_kutubxonani_aniqla,
)

User = get_user_model()


class RegisterThrottle(AnonRateThrottle):
    scope = "register"
    rate = "10/hour"


class PasswordResetThrottle(AnonRateThrottle):
    scope = "password_reset"
    rate = "10/hour"


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={"request": request})
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
    http_method_names = ["get", "patch", "post", "delete"]

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

    @action(
        detail=True,
        methods=["post", "delete"],
        url_path="logo",
        parser_classes=[MultiPartParser],
    )
    def logo(self, request, pk=None):
        """POST a logo image (field `file`) or DELETE to remove it."""
        org = self.get_queryset().filter(pk=pk).first()
        if not org:
            return Response({"detail": "Kutubxona topilmadi."}, status=404)
        azolik = foydalanuvchi_azoligi(request.user, org)
        if not request.user.is_superuser and not (azolik and azolik.adminmi):
            return Response({"detail": "Ruxsat yo'q."}, status=403)
        if request.method == "DELETE":
            remove_old_logos(org)
            org.logo_url = ""
        else:
            upload = request.FILES.get("file")
            if upload is None:
                return Response({"file": "Rasm faylini tanlang."}, status=400)
            try:
                org.logo_url = save_logo(org, upload)
            except LogoError as exc:
                return Response({"file": str(exc)}, status=400)
        org.save(update_fields=["logo_url"])
        return Response(OrganizationSerializer(org, context={"request": request}).data)

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
    http_method_names = ["get", "post", "patch", "delete"]
    filterset_fields = ["status", "type", "faol"]
    search_fields = ["nomi", "slug", "email", "telefon"]

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "request": self.request}

    def perform_create(self, serializer):
        org = serializer.save()
        log_action(
            "organization.created_by_platform",
            actor=self.request.user,
            organization=org,
            target_type="organization",
            target_id=org.pk,
            metadata={"nomi": org.nomi},
            request=self.request,
        )

    def perform_update(self, serializer):
        org = serializer.save()
        log_action(
            "organization.updated_by_platform",
            actor=self.request.user,
            organization=org,
            target_type="organization",
            target_id=org.pk,
            metadata={"fields": sorted(serializer.validated_data)},
            request=self.request,
        )

    def destroy(self, request, *args, **kwargs):
        """Hard delete — only for archived organizations, and only when no protected data blocks it."""
        from django.db.models import ProtectedError

        org = self.get_object()
        if org.status != Organization.HOLAT_ARCHIVED:
            return Response({"detail": "O'chirishdan oldin tashkilotni arxivlang."}, status=409)
        nomi, pk = org.nomi, org.pk
        try:
            org.delete()
        except ProtectedError:
            return Response(
                {"detail": "Tashkilotda bog'langan ma'lumotlar bor, o'chirib bo'lmaydi. Arxivlangan holda qoldiring."},
                status=409,
            )
        log_action(
            "organization.deleted",
            actor=request.user,
            target_type="organization",
            target_id=pk,
            metadata={"nomi": nomi},
            request=request,
        )
        return Response(status=204)

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
        serializer = SubscriptionChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        plan_code = data.get("plan")
        # A deactivated plan stays with the organizations that already have it.
        if plan_code and plan_code != obuna.plan.code:
            plan = SubscriptionPlan.objects.filter(code=plan_code, faol=True).first()
            if not plan:
                return Response({"detail": "Tarif rejasi topilmadi."}, status=404)
            obuna.plan = plan
        for field in ("status", "trial_ends_at", "current_period_end"):
            if field in data:
                setattr(obuna, field, data[field])
        obuna.save()
        log_action(
            "organization.subscription_changed",
            actor=request.user,
            organization=org,
            target_type="organization_subscription",
            target_id=obuna.pk,
            metadata={
                "plan": obuna.plan.code,
                "plan_name": obuna.plan.nomi,
                "status": obuna.status,
            },
            request=request,
        )
        return Response(
            SaaSOrganizationSerializer(org, context={"request": request}).data
        )

    @staticmethod
    def _subscription_summary(org):
        # Read only: an organization without a subscription row is not given one here.
        sub = getattr(org, "subscription", None)
        if sub is None:
            return None
        return {
            "plan": sub.plan.code,
            "plan_name": sub.plan.nomi,
            "status": sub.status,
            "effective_status": sub.samarali_holat,
            "trial_ends_at": sub.trial_ends_at,
            "current_period_end": sub.current_period_end,
            "limits": {
                "max_staff": sub.plan.max_staff,
                "max_resources": sub.plan.max_resources,
                "max_customers": sub.plan.max_customers,
            },
        }

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
        for org in self.get_queryset().select_related("subscription__plan", "telegram_bot"):
            data.append(
                {
                    "id": org.id,
                    "nomi": org.nomi,
                    "slug": org.slug,
                    "type": org.type,
                    "status": org.status,
                    "faol": org.faol,
                    "kitoblar": Kitob.objects.filter(organization=org).count(),
                    "oquvchilar": Oquvchi.objects.filter(organization=org).count(),
                    "berishlar": Berish.objects.filter(organization=org).count(),
                    "azoliklar": Membership.objects.filter(organization=org, faol=True).count(),
                    "bot_ulangan": hasattr(org, "telegram_bot"),
                    "egasi_ismi": org.egasi.full_name if org.egasi_id else "",
                    "telefon": org.telefon,
                    "status_reason": org.status_reason,
                    "yaratilgan": org.yaratilgan,
                    "subscription": self._subscription_summary(org),
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
    """Tariff plans: platform admins only."""

    # Meta.ordering is ignored by GROUP BY queries, so the order is explicit.
    queryset = SubscriptionPlan.objects.annotate(
        organization_count=Count("obunalar")
    ).order_by("tartib", "narx_oylik", "nomi")
    permission_classes = [IsPlatformAdmin]
    pagination_class = None
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        from .serializers import SubscriptionPlanSerializer

        return SubscriptionPlanSerializer

    def _log(self, action_name, plan, plan_id=None):
        log_action(
            action_name,
            actor=self.request.user,
            target_type="subscription_plan",
            target_id=plan_id or plan.pk,
            metadata={"code": plan.code, "name": plan.nomi},
            request=self.request,
        )

    def perform_create(self, serializer):
        self._log("plan.created", serializer.save())

    def perform_update(self, serializer):
        self._log("plan.updated", serializer.save())

    def destroy(self, request, *args, **kwargs):
        from django.db.models import ProtectedError

        plan = self.get_object()
        if plan.code == DEFAULT_PLAN_CODE:
            return Response({"detail": "Boshlang'ich tarifni o'chirib bo'lmaydi."}, status=409)
        plan_id = plan.pk
        try:
            plan.delete()
        except ProtectedError:
            return Response(
                {"detail": "Bu tarifdan foydalanayotgan tashkilotlar bor. Avval ularni boshqa tarifga o'tkazing."},
                status=409,
            )
        self._log("plan.deleted", plan, plan_id)
        return Response(status=204)


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
@throttle_classes([PasswordResetThrottle])
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
@throttle_classes([PasswordResetThrottle])
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
    data = dict(OrganizationSerializer(org, context={"request": request}).data)
    # Platform contacts for the blocking status screen; empty values are hidden there.
    data["support"] = {
        "phone": settings.SUPPORT_PHONE,
        "telegram": settings.SUPPORT_TELEGRAM,
    }
    return Response(data)


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


@api_view(["GET"])
@permission_classes([AllowAny])
def push_public_key(request):
    from django.conf import settings

    return Response({"public_key": settings.VAPID_PUBLIC_KEY or None})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def push_subscribe(request):
    """Save the browser's Web Push subscription for the current user and the
    organization they belong to (works while the organization is still pending)."""
    from .models import PushSubscription

    endpoint = str(request.data.get("endpoint", "")).strip()
    keys = request.data.get("keys") or {}
    p256dh = str(keys.get("p256dh", "")).strip()
    auth = str(keys.get("auth", "")).strip()
    if not (endpoint and p256dh and auth):
        return Response({"detail": "Obuna ma'lumoti to'liq emas."}, status=400)
    org = joriy_kutubxonani_aniqla(request, required=False, allow_inactive=True)
    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={"user": request.user, "organization": org, "p256dh": p256dh, "auth": auth},
    )
    return Response({"subscribed": True}, status=201)


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Public liveness probe for uptime monitors (no tenant data)."""
    from .health import liveness

    data = liveness()
    return Response(data, status=200 if data["status"] == "ok" else 503)


@api_view(["GET"])
@permission_classes([IsPlatformAdmin])
def platform_health(request):
    """Detailed component, heartbeat and bot status for the platform panel."""
    from .health import bots_status, check_cache, check_database, heartbeat_status

    db_ok, db_err = check_database()
    cache_ok, cache_err = check_cache()
    return Response(
        {
            "checked_at": timezone.now(),
            "web": {"status": "ok"},
            "database": {"status": "ok" if db_ok else "down", "error": db_err},
            "cache": {"status": "ok" if cache_ok else "down", "error": cache_err},
            "heartbeats": heartbeat_status(),
            "bots": bots_status(),
        }
    )


class IssueReportThrottle(AnonRateThrottle):
    """Anonymous and authenticated clients: max 10 reports per hour."""

    scope = "issue_report"

    def get_rate(self):
        return "10/hour"

    def get_cache_key(self, request, view):
        ident = request.user.pk if request.user and request.user.is_authenticated else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


@api_view(["POST"])
@permission_classes([AllowAny])  # login/register errors must be reportable too
def issue_report_create(request):
    """Store a problem report with auto-collected diagnostics."""
    from .models import IssueReport
    from .serializers import IssueReportSerializer

    for throttle in (IssueReportThrottle(),):
        if not throttle.allow_request(request, None):
            return Response({"detail": "Juda ko'p xabar yuborildi. Keyinroq urinib ko'ring."}, status=429)
    serializer = IssueReportSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = request.user if request.user.is_authenticated else None
    org = joriy_kutubxonani_aniqla(request, required=False, allow_inactive=True) if user else None
    serializer.save(user=user, organization=org)
    return Response({"id": serializer.instance.pk}, status=201)
