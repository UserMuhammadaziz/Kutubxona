"""Subscription billing: price, checkout through Taps, and applying payments."""

import calendar
import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from organization.models import OrganizationSubscription, SubscriptionPlan
from organization.services import log_action, subscription_for

from . import taps
from .models import Payment

logger = logging.getLogger(__name__)

PERIODS = (1, 3, 6, 12)
# An unpaid checkout is dropped after this long.
PENDING_TTL = timedelta(hours=2)


def paid_plans():
    return SubscriptionPlan.objects.filter(faol=True, narx_oylik__gt=0)


def discount_percent(months):
    return int(settings.BILLING_DISCOUNTS.get(str(months), settings.BILLING_DISCOUNTS.get(months, 0)) or 0)


def price(plan, months):
    """Total in so'm for `months` of `plan`, after the period discount, rounded to 1000."""
    full = int(plan.narx_oylik) * months
    total = full * (100 - discount_percent(months)) // 100
    return int(round(total / 1000.0) * 1000) if total >= 1000 else total


def add_months(moment, months):
    month = moment.month - 1 + months
    year = moment.year + month // 12
    month = month % 12 + 1
    day = min(moment.day, calendar.monthrange(year, month)[1])
    return moment.replace(year=year, month=month, day=day)


def is_expired(organization):
    """True only for a subscription row whose effective state is not active/trial."""
    sub = OrganizationSubscription.objects.filter(organization=organization).first()
    return bool(sub) and not sub.faolmi


def create_checkout(organization, plan, months, method, user):
    amount = price(plan, months)
    payment = Payment.objects.create(
        organization=organization,
        plan=plan,
        months=months,
        amount=amount,
        method=method,
        created_by=user if getattr(user, "is_authenticated", False) else None,
    )
    try:
        data = taps.create_donation(method=method, amount=amount, note=f"kutubxona:{organization.pk}:{payment.pk}")
    except taps.TapsError as error:
        logger.warning("billing: create failed for payment %s: %s", payment.pk, error)
        Payment.objects.filter(pk=payment.pk).update(status=Payment.STATUS_CANCELLED, status_reason="create_failed")
        raise
    payment.provider_payment_id = str(data.get("donationId") or "")
    payment.checkout_url = str(data.get("checkoutUrl") or "")[:1000]
    payment.meta = {"total": data.get("totalAmount"), "commission": data.get("commissionAmount")}
    if not payment.provider_payment_id or not payment.checkout_url:
        payment.status = Payment.STATUS_CANCELLED
        payment.status_reason = "bad_provider_answer"
        payment.save()
        raise taps.TapsError("taps: no donationId/checkoutUrl")
    payment.save()
    log_action(
        "billing.checkout_created",
        actor=user,
        organization=organization,
        target_type="payment",
        target_id=payment.pk,
        metadata={"months": months, "amount": amount, "method": method, "plan": plan.code},
    )
    return payment


def _apply(payment, data, now):
    """Mark paid and extend the subscription. Runs once per payment (row lock)."""
    with transaction.atomic():
        locked = Payment.objects.select_for_update().get(pk=payment.pk)
        if locked.status != Payment.STATUS_PENDING:
            return locked.status
        sub = subscription_for(locked.organization)
        sub = OrganizationSubscription.objects.select_for_update().get(pk=sub.pk)
        # Paid time is added on top of what is left, so paying early loses nothing.
        current_end = sub.current_period_end if sub.status in ("active", "past_due") else None
        trial_end = sub.trial_ends_at if sub.status == "trial" else None
        base = max([moment for moment in (now, current_end, trial_end) if moment])
        sub.plan = locked.plan
        sub.status = "active"
        sub.current_period_end = add_months(base, locked.months)
        sub.cancel_at_period_end = False
        sub.save()
        locked.status = Payment.STATUS_PAID
        locked.paid_at = now
        locked.period_end = sub.current_period_end
        locked.meta = {**locked.meta, "status": data.get("status"), "paid_time": data.get("paidTime"), "paid_total": data.get("amount")}
        locked.save()
    log_action(
        "billing.payment_paid",
        organization=locked.organization,
        target_type="payment",
        target_id=locked.pk,
        metadata={"months": locked.months, "amount": locked.amount, "period_end": locked.period_end.isoformat()},
    )
    return locked.status


def sync_payment(payment, now=None):
    """Compare a pending payment with Taps. Returns the (possibly new) status."""
    now = now or timezone.now()
    if payment.status != Payment.STATUS_PENDING or not payment.provider_payment_id:
        return payment.status
    data = taps.donation_status(payment.provider_payment_id)
    if taps.is_paid(data):
        if taps.paid_amount(data) < payment.amount:
            logger.warning("billing: paid amount too low for payment %s: %s", payment.pk, data.get("amount"))
            return payment.status
        return _apply(payment, data, now)
    if taps.is_dead(data) or now - payment.created_at > PENDING_TTL:
        reason = f"taps: {data.get('status')}" if taps.is_dead(data) else "expired"
        Payment.objects.filter(pk=payment.pk, status=Payment.STATUS_PENDING).update(
            status=Payment.STATUS_CANCELLED, status_reason=reason[:255]
        )
        return Payment.STATUS_CANCELLED
    return payment.status


def sync_pending(limit=50):
    done = 0
    for payment in Payment.objects.filter(status=Payment.STATUS_PENDING).exclude(provider_payment_id="")[:limit]:
        try:
            sync_payment(payment)
            done += 1
        except taps.TapsError as error:
            logger.warning("billing: sync %s failed: %s", payment.pk, error)
    return done
