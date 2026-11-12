from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class LoginThrottle(AnonRateThrottle):
    scope = "login"


class ThrottledTokenView(TokenObtainPairView):
    """Parol terishdan himoya: IP bo'yicha daqiqasiga 10 urinish (Redis'da umumiy)."""

    throttle_classes = [LoginThrottle]
from berish.views import BerishViewSet
from jarima.views import JarimaViewSet
from kitob.views import BandQilishViewSet, KitobViewSet
from navbat.views import NavbatViewSet
from nusxa.views import NusxaViewSet
from organization.views import (
    OrganizationViewSet,
    RegisterView,
    SaaSOrganizationViewSet,
    current_organization,
    my_memberships,
    password_reset_confirm,
    password_reset_request,
)
from oquvchi.views import OquvchiViewSet, ArizaViewSet
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
router.register("loans", BerishViewSet, basename="loans")
router.register("fines", JarimaViewSet, basename="fines")
router.register("reservations", NavbatViewSet, basename="reservations")
router.register("holds", BandQilishViewSet, basename="holds")
router.register("staff", UserViewSet, basename="staff")
router.register("organizations", OrganizationViewSet, basename="organizations")
router.register("saas/organizations", SaaSOrganizationViewSet, basename="saas-organizations")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/stats/", include("stats.urls")),
    path("api/auth/token/", ThrottledTokenView.as_view()),
    path("api/auth/token/refresh/", TokenRefreshView.as_view()),
    path("api/auth/me/", me),
    path("api/auth/register/", RegisterView.as_view()),
    path("api/auth/logout/", LogoutView.as_view()),
    path("api/auth/password-reset/", password_reset_request),
    path("api/auth/password-reset/confirm/", password_reset_confirm),
    path("api/auth/organization/", current_organization),
    path("api/auth/memberships/", my_memberships),
    path("api/telegram/settings/", TelegramBotSettingsView.as_view()),
    path("api/telegram/actions/<str:action>/", TelegramBotActionView.as_view()),
    path("api/telegram/webhook/<str:path>/", TelegramWebhookView.as_view()),
    path("", include("web.urls")),
]
