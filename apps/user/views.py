from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from organization.models import Membership
from organization.services import check_limit, log_action
from organization.tenancy import joriy_kutubxonani_aniqla, legacy_rejimmi
from .models import User
from .permissions import IsAdmin
from .serializers import UserSerializer, UserCreateSerializer


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


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    """GET /api/auth/me/ — joriy foydalanuvchi va kutubxonalari."""
    return Response(UserSerializer(request.user, context={"request": request}).data)
