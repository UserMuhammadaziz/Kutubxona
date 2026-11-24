from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class LoginThrottle(AnonRateThrottle):
    scope = "login"


class ThrottledTokenView(TokenObtainPairView):
    """Parol terishdan himoya: IP bo'yicha daqiqasiga 10 urinish (Redis'da umumiy)."""

    throttle_classes = [LoginThrottle]

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except AuthenticationFailed:
            # Say exactly what is wrong instead of simplejwt's generic English message.
            error, detail = self._specific_error(request.data.get("username"), request.data.get("password"))
            return Response({"error": error, "detail": detail}, status=401)

    @staticmethod
    def _specific_error(username, password):
        if not username or not password:
            return "login_yoki_parol_bosh", "Login va parolni kiriting"
        user = get_user_model().objects.filter(username=str(username)).first()
        if user is None:
            return "login_topilmadi", f"«{username}» logini bilan foydalanuvchi topilmadi"
        if not user.is_active:
            return "akkaunt_nofaol", "Akkaunt o'chirilgan yoki faol emas. Administratorga murojaat qiling"
        return "parol_notogri", "Parol noto'g'ri"
from announcement.views import AnnouncementViewSet
from berish.views import BerishViewSet
from jarima.views import JarimaViewSet
from kitob.views import BandQilishViewSet, KitobViewSet
from navbat.views import NavbatViewSet
from nusxa.views import NusxaViewSet
from organization.views import (
    AuditLogViewSet,
    SubscriptionPlanViewSet,
    OrganizationViewSet,
    RegisterView,
    SaaSOrganizationViewSet,
    current_organization,
    issue_report_create,
    health,
    platform_health,
    my_memberships,
    password_reset_confirm,
    password_reset_request,
    push_public_key,
    push_subscribe,
)
from oquvchi.views import ArizaViewSet, FanViewSet, OquvchiViewSet
from telegrambot.views import (
    TelegramBotActionView,
    TelegramBotSettingsView,
    TelegramWebhookView,
)
from user.views import LogoutView, UserViewSet, me

router = DefaultRouter()
router.register("books", KitobViewSet, basename="books")
router.register("copies", NusxaViewSet, basename="copies")
router.register("readers", OquvchiViewSet, basename="readers")
router.register("applications", ArizaViewSet, basename="applications")
router.register("subjects", FanViewSet, basename="subjects")
router.register("loans", BerishViewSet, basename="loans")
router.register("fines", JarimaViewSet, basename="fines")
router.register("reservations", NavbatViewSet, basename="reservations")
router.register("holds", BandQilishViewSet, basename="holds")
router.register("announcements", AnnouncementViewSet, basename="announcements")
router.register("staff", UserViewSet, basename="staff")
router.register("organizations", OrganizationViewSet, basename="organizations")
router.register("saas/organizations", SaaSOrganizationViewSet, basename="saas-organizations")
router.register("saas/plans", SubscriptionPlanViewSet, basename="saas-plans")
router.register("saas/audit", AuditLogViewSet, basename="saas-audit")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/stats/", include("stats.urls")),
    path("api/health/", health),
    path("api/saas/health/", platform_health),
    path("api/auth/token/", ThrottledTokenView.as_view()),
    path("api/auth/token/refresh/", TokenRefreshView.as_view()),
    path("api/auth/me/", me),
    path("api/auth/register/", RegisterView.as_view()),
    path("api/auth/logout/", LogoutView.as_view()),
    path("api/auth/password-reset/", password_reset_request),
    path("api/auth/password-reset/confirm/", password_reset_confirm),
    path("api/auth/organization/", current_organization),
    path("api/auth/memberships/", my_memberships),
    path("api/issue-reports/", issue_report_create),
    path("api/push/public-key/", push_public_key),
    path("api/push/subscribe/", push_subscribe),
    path("api/telegram/settings/", TelegramBotSettingsView.as_view()),
    path("api/telegram/actions/<str:action>/", TelegramBotActionView.as_view()),
    path("api/telegram/webhook/<str:path>/", TelegramWebhookView.as_view()),
    path("", include("web.urls")),
]
