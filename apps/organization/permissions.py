from rest_framework.permissions import BasePermission

from .tenancy import joriy_kutubxonani_aniqla, kutubxona_roli


class IsPlatformAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.is_staff)
        )


class KutubxonaAdmin(BasePermission):
    def has_permission(self, request, view):
        org = joriy_kutubxonani_aniqla(request, required=False)
        rol = kutubxona_roli(request.user, org)
        return rol in ("egasi", "administrator")
