"""Tashkilot (tenant) hayot sikli, obuna va audit xizmatlari."""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import AuditLog, Organization, OrganizationSubscription, SubscriptionPlan

DEFAULT_TRIAL_KUN = 14


def _client_ip(request):
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(
    action,
    *,
    actor=None,
    organization=None,
    target_type="",
    target_id="",
    metadata=None,
    request=None,
):
    """Muhim amalni audit jurnaliga yozadi.

    Audit yozuvi hech qachon asosiy amalni buzmasligi kerak: xatolik
    yuz bersa, uni yutamiz (lekin amal bajarilgan bo'lib qoladi).
    """
    try:
        return AuditLog.objects.create(
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            organization=organization,
            action=action,
            target_type=target_type,
            target_id=str(target_id or ""),
            metadata=metadata or {},
            ip_address=_client_ip(request),
        )
    except Exception:
        return None


def free_plan():
    return SubscriptionPlan.objects.filter(code="free").first()


def subscription_for(organization, *, trial=True):
    """Tashkilot obunasini qaytaradi; bo'lmasa Free tarifda yaratadi."""
    plan = free_plan()
    if plan is None:
        plan = SubscriptionPlan.objects.create(
            code="free",
            nomi="Free",
            narx_oylik=0,
            max_staff=3,
            max_resources=500,
            max_customers=500,
            tartib=1,
        )
    obuna, yaratildi = OrganizationSubscription.objects.get_or_create(
        organization=organization,
        defaults={
            "plan": plan,
            "status": "trial" if trial else "active",
            "trial_ends_at": (
                timezone.now() + timedelta(days=DEFAULT_TRIAL_KUN) if trial else None
            ),
        },
    )
    return obuna


def plan_limit(organization, field):
    """Obuna rejasidagi limitni qaytaradi (`None` — cheksiz)."""
    obuna = subscription_for(organization)
    return getattr(obuna.plan, field, None)


def check_limit(organization, field, current_count):
    limit = plan_limit(organization, field)
    if limit is not None and current_count >= limit:
        raise ValidationError(
            {
                "error": "obuna_limiti",
                "detail": (
                    f"Tarif rejasi limiti tugagan ({limit}). "
                    "Davom etish uchun tarifni yangilang."
                ),
                "limit": limit,
            }
        )


@transaction.atomic
def set_status(organization, status, *, actor=None, reason="", request=None):
    """Tashkilot holatini o'zgartiradi va audit yozadi.

    Ruxsat etilgan o'tishlar ataylab keng: platforma administratori
    xato holatni ham tuzata olishi kerak. Biznes cheklovlari view
    qatlamida qo'shimcha tekshiriladi.
    """
    if status not in dict(Organization.HOLAT_CHOICES):
        raise ValidationError({"status": "Noma'lum tashkilot holati."})

    organization.status = status
    organization.status_reason = reason or ""
    organization.status_changed_at = timezone.now()
    if status == Organization.HOLAT_ACTIVE:
        organization.approved_at = organization.approved_at or timezone.now()
        organization.approved_by = actor if getattr(actor, "is_authenticated", False) else None
    organization.save(
        update_fields=[
            "status",
            "status_reason",
            "status_changed_at",
            "approved_at",
            "approved_by",
            "faol",
        ]
    )
    log_action(
        f"organization.{status}",
        actor=actor,
        organization=organization,
        target_type="organization",
        target_id=organization.pk,
        metadata={"reason": reason},
        request=request,
    )
    return organization


def active_subscription(organization):
    return subscription_for(organization)
