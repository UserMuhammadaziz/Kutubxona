from rest_framework.permissions import BasePermission

from organization.tenancy import (
    joriy_kutubxonani_aniqla,
    kutubxona_roli,
    legacy_rejimmi,
)


class IsLibrarian(BasePermission):
    """Kutubxonachi, administrator yoki kutubxona egasi."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        org = joriy_kutubxonani_aniqla(request, required=False)
        rol = kutubxona_roli(request.user, org)
        if rol is not None:
            return rol in ("egasi", "administrator", "kutubxonachi")
        # Bo'sh (legacy/test) bazada eski global rol ishlatiladi.
        return legacy_rejimmi() and request.user.rol in ("kutubxonachi", "administrator")


class IsAdmin(BasePermission):
    """Faqat kutubxona egasi yoki administratori."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        org = joriy_kutubxonani_aniqla(request, required=False)
        rol = kutubxona_roli(request.user, org)
        if rol is not None:
            return rol in ("egasi", "administrator")
        return legacy_rejimmi() and request.user.rol == "administrator"
