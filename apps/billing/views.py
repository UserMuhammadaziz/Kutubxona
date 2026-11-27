from django.conf import settings
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from organization.services import subscription_for
from organization.tenancy import joriy_kutubxonani_aniqla, kutubxona_roli

from . import taps
from .models import Payment
from .services import PERIODS, create_checkout, discount_percent, paid_plans, price, sync_payment


class CheckoutThrottle(ScopedRateThrottle):
    scope = "billing"


def _admin_org(request):
    org = joriy_kutubxonani_aniqla(request, allow_unpaid=True)
    if org is None or kutubxona_roli(request.user, org) not in ("egasi", "administrator"):
        raise PermissionDenied("Obunani faqat kutubxona egasi yoki administratori boshqaradi.")
    return org


def _payment(payment):
    parts = list(payment.parts.all())
    current = next((part for part in parts if part.status == Payment.STATUS_PENDING), None)
    return {
        "id": payment.pk,
        "plan": payment.plan.code,
        "plan_name": payment.plan.nomi,
        "months": payment.months,
        "amount": payment.amount,
        "method": payment.method,
        "method_name": taps.METHODS.get(payment.method, (None, payment.method))[1],
        "status": payment.status,
        "checkout_url": current.checkout_url if current and payment.status == Payment.STATUS_PENDING else "",
        "parts_total": len(parts),
        "parts_paid": sum(part.status == Payment.STATUS_PAID for part in parts),
        "part_amount": current.amount if current else None,
        "created_at": payment.created_at,
        "paid_at": payment.paid_at,
        "period_end": payment.period_end,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def overview(request):
    org = _admin_org(request)
    sub = subscription_for(org)
    plans = [
        {
            "code": plan.code,
            "name": plan.nomi,
            "monthly_price": int(plan.narx_oylik),
            "periods": [
                {"months": months, "amount": price(plan, months), "discount": discount_percent(months)}
                for months in PERIODS
            ],
        }
        for plan in paid_plans()
    ]
    return Response(
        {
            "subscription": {
                "plan": sub.plan.code,
                "plan_name": sub.plan.nomi,
                "status": sub.samarali_holat,
                "trial_ends_at": sub.trial_ends_at,
                "current_period_end": sub.current_period_end,
            },
            "plans": plans,
            "methods": [{"code": code, "name": name} for code, (_, name) in taps.METHODS.items()],
            "enforced": settings.BILLING_ENFORCE,
            "max_part_amount": settings.TAPS_MAX_AMOUNT,
            "payments": [_payment(p) for p in Payment.objects.filter(organization=org).select_related("plan").prefetch_related("parts")[:20]],
        }
    )


class CheckoutSerializer(serializers.Serializer):
    plan = serializers.CharField(required=False, allow_blank=True)
    months = serializers.ChoiceField(choices=PERIODS)
    method = serializers.ChoiceField(choices=list(taps.METHODS))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([CheckoutThrottle])
def checkout(request):
    org = _admin_org(request)
    data = CheckoutSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    plans = paid_plans()
    code = data.validated_data.get("plan")
    plan = plans.filter(code=code).first() if code else plans.first()
    if plan is None:
        return Response({"error": "plan_not_found", "detail": "Pullik tarif topilmadi."}, status=404)
    try:
        payment = create_checkout(org, plan, data.validated_data["months"], data.validated_data["method"], request.user)
    except taps.TapsError:
        return Response(
            {"error": "provider", "detail": "To'lov tizimi javob bermadi. Birozdan keyin qayta urinib ko'ring."},
            status=502,
        )
    return Response(_payment(payment), status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_detail(request, pk):
    org = _admin_org(request)
    payment = Payment.objects.select_related("plan", "organization").filter(organization=org, pk=pk).first()
    if payment is None:
        return Response({"error": "not_found", "detail": "To'lov topilmadi."}, status=404)
    try:
        sync_payment(payment, renew=True)
    except taps.TapsError:
        pass  # keep the last known status; the background task retries
    payment.refresh_from_db()
    return Response(_payment(payment))
