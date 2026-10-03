from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from berish.views import BerishViewSet
from jarima.views import JarimaViewSet
from kitob.views import BandQilishViewSet, KitobViewSet
from navbat.views import NavbatViewSet
from nusxa.views import NusxaViewSet
from oquvchi.views import OquvchiViewSet, ArizaViewSet
from user.views import UserViewSet, me

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

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/stats/", include("stats.urls")),
    path("api/auth/token/", TokenObtainPairView.as_view()),
    path("api/auth/token/refresh/", TokenRefreshView.as_view()),
    path("api/auth/me/", me),
    path("", include("web.urls")),
]
