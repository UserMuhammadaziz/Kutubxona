from django.db import models
from django.db.models import QuerySet
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Membership, Organization


def legacy_rejimmi():
    """Bazada hali birorta kutubxona yo'q bo'lsa — eski/test rejimi.

    Bu holat faqat bo'sh bazada yoki eski testlarda uchraydi. Data migration
    mavjud ma'lumotlarni bitta kutubxonaga bog'laydi, shundan keyin bu
    funksiya doim False qaytaradi.
    """
    return not Organization.objects.exists()


def foydalanuvchi_kutubxonalari(user):
    if not getattr(user, "is_authenticated", False):
        return Organization.objects.none()
    if user.is_superuser:
        return Organization.objects.filter(a_zolar__faol=True).distinct()
    return Organization.objects.filter(a_zolar__user=user, a_zolar__faol=True).distinct()


def foydalanuvchi_azoligi(user, organization):
    if not getattr(user, "is_authenticated", False) or organization is None:
        return None
    return (
        Membership.objects.select_related("organization", "user")
        .filter(user=user, organization=organization, faol=True)
        .first()
    )


def _holatni_tekshir(org, allow_inactive=False):
    """Tashkilot holati bo'yicha kirishni tekshiradi.

    PENDING / REJECTED / SUSPENDED / ARCHIVED tashkilot ma'lumotlariga
    kirish yopiq. Platforma administratori boshqaruv endpointlari orqali
    ishlaydi, tenant API'lariga esa faqat faol tashkilot bilan kiradi.
    """
    if org is None:
        return None
    if allow_inactive or org.status == Organization.HOLAT_ACTIVE:
        return org
    raise PermissionDenied(
        {
            "error": f"organization_{org.status}",
            "detail": {
                Organization.HOLAT_PENDING: (
                    "Tashkilotingiz hali platforma administratori tomonidan "
                    "tasdiqlanmagan."
                ),
                Organization.HOLAT_REJECTED: "Tashkilot arizasi rad etilgan.",
                Organization.HOLAT_SUSPENDED: "Tashkilot faoliyati to'xtatilgan.",
                Organization.HOLAT_ARCHIVED: "Tashkilot arxivlangan.",
            }.get(org.status, "Tashkilot faol emas."),
            "status": org.status,
        }
    )


def joriy_kutubxonani_aniqla(request, required=True, allow_inactive=False):
    """So'rov uchun kutubxonani xavfsiz aniqlaydi.

    Tartib:
    1. `X-Organization-Id` sarlavhasi (faqat a'zolik bo'lsa);
    2. foydalanuvchining yagona a'zoligi;
    3. bir nechta a'zolik bo'lsa — sarlavha talab qilinadi;
    4. baza bo'sh bo'lsa — legacy rejim (`None`).

    `organization_id` hech qachon mijozdan ishonchli manba sifatida
    qabul qilinmaydi: u faqat foydalanuvchining a'zoligi bilan
    kesishganda ishlatiladi.
    """
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        if required:
            raise PermissionDenied("Avval tizimga kiring.")
        return None

    # Barcha a'zoliklar (holatidan qat'i nazar) — pending holatini ham
    # aniq xabar bilan qaytarish uchun kerak.
    barcha = foydalanuvchi_kutubxonalari(user)
    org_id = request.headers.get("X-Organization-Id") or request.query_params.get(
        "organization_id"
    )
    if org_id:
        try:
            org_id = int(org_id)
        except (TypeError, ValueError):
            raise ValidationError({"organization": "Kutubxona ID noto'g'ri."})
        if user.is_superuser:
            org = Organization.objects.filter(pk=org_id).first()
        else:
            org = barcha.filter(pk=org_id).first()
        if not org:
            raise PermissionDenied("Bu kutubxonaga kirish huquqingiz yo'q.")
        return _holatni_tekshir(org, allow_inactive)

    azoliklar = (
        barcha
        if allow_inactive
        else barcha.filter(status=Organization.HOLAT_ACTIVE)
    )
    if azoliklar.count() == 1:
        return azoliklar.first()

    if user.is_superuser:
        org = azoliklar.first()
        if org:
            return org
        org = Organization.objects.filter(status=Organization.HOLAT_ACTIVE).first()
        if org:
            return org

    if legacy_rejimmi() and not required:
        return None

    # Bitta a'zolik bor, lekin u faol emas — aniq sabab bilan 403.
    if not allow_inactive and barcha.count() == 1:
        return _holatni_tekshir(barcha.first(), allow_inactive)

    if azoliklar.exists():
        raise ValidationError(
            {"organization": "Qaysi kutubxonada ishlayotganingizni tanlang."}
        )
    if required:
        raise PermissionDenied("Siz hech qanday faol kutubxonaga a'zo emassiz.")
    return None


def kutubxona_roli(user, organization):
    if organization is None:
        return None
    if user.is_superuser:
        return "administrator"
    azolik = foydalanuvchi_azoligi(user, organization)
    return azolik.rol if azolik else None


def scope(qs, organization):
    """Queryset'ni kutubxonaga cheklaydi.

    `organization is None` — faqat bo'sh (legacy/test) bazada ruxsat etiladi.
    Baza bo'sh bo'lmasa, tenant aniqlanmagan so'rov hech qanday yozuv
    ko'rmaydi (fail-closed).
    """
    if organization is None:
        return qs if legacy_rejimmi() else qs.none()
    return qs.filter(organization=organization)


def organization_from_value(value):
    if value is None:
        return None
    if isinstance(value, Organization):
        return value
    if isinstance(value, int):
        return Organization.objects.filter(pk=value).first()
    if isinstance(value, str) and value.isdigit():
        return Organization.objects.filter(pk=int(value)).first()
    if isinstance(value, str):
        return Organization.objects.filter(slug=value).first()
    return None


class TenantViewSetMixin:
    """ModelViewSet uchun tenant chegaralarini qo'llaydi.

    ViewSet'da `organization_field` yoki modeldagi `organization` maydoni
    bo'lishi kerak. Barcha list/retrieve/update/delete so'rovlari joriy
    kutubxona bilan cheklanadi; yaratishda organization avtomatik qo'yiladi.
    """

    organization = None

    def get_organization(self):
        if self.organization is None:
            self.organization = joriy_kutubxonani_aniqla(self.request, required=True)
        return self.organization

    def get_queryset(self):
        qs = super().get_queryset()
        return scope(qs, self.get_organization())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["organization"] = self.get_organization()
        return context

    def perform_create(self, serializer):
        serializer.save(organization=self.get_organization())

    def perform_update(self, serializer):
        serializer.save(organization=self.get_organization())


class TenantSerializerMixin:
    """Bog'langan obyektlar ham aynan shu kutubxonadan ekanini ta'minlaydi."""

    def _organization(self):
        org = self.context.get("organization")
        request = self.context.get("request")
        if org is None and request is not None:
            org = getattr(request, "organization", None)
        return org

    def get_fields(self):
        fields = super().get_fields()
        org = self._organization()
        if org is None:
            return fields
        for field in fields.values():
            qs = getattr(field, "queryset", None)
            if isinstance(qs, QuerySet) and hasattr(qs.model, "organization"):
                field.queryset = qs.filter(organization=org)
        return fields
