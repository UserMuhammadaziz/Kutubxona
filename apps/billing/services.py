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
from .models import Payment, PaymentPart

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


def split_amount(total, cap):
    """Equal parts not above `cap`, rounded to 1000 so'm; the last part takes the rest."""
    if total <= cap:
        return [total]
    count = -(-total // cap)
    part = -(-total // count // 1000) * 1000
    parts = [part] * (count - 1)
    parts.append(total - sum(parts))
    return parts


def _open_part(part, payment):
    """Create the Taps donation for one part and mirror its link on the payment."""
    data = taps.create_donation(
        method=payment.method,
        amount=part.amount,
        note=f"kutubxona:{payment.organization_id}:{payment.pk}:{part.index}",
    )
    donation_id = str(data.get("donationId") or "")
    url = str(data.get("checkoutUrl") or "")[:1000]
    if not donation_id or not url:
        raise taps.TapsError("taps: no donationId/checkoutUrl")
    if part.provider_payment_id:
        # An older link may still be paid later: keep checking it.
        part.meta = {**part.meta, "previous_ids": [*part.meta.get("previous_ids", []), part.provider_payment_id]}
    part.provider_payment_id = donation_id
    part.checkout_url = url
    part.created_at = timezone.now()
    part.meta = {**part.meta, "total": data.get("totalAmount"), "commission": data.get("commissionAmount")}
    part.save()
    payment.provider_payment_id = donation_id
    payment.checkout_url = url
    payment.save(update_fields=["provider_payment_id", "checkout_url"])


def create_checkout(organization, plan, months, method, user):
    amount = price(plan, months)
    with transaction.atomic():
        payment = Payment.objects.create(
            organization=organization,
            plan=plan,
            months=months,
            amount=amount,
            method=method,
            created_by=user if getattr(user, "is_authenticated", False) else None,
        )
        for index, part_amount in enumerate(split_amount(amount, settings.TAPS_MAX_AMOUNT), start=1):
            PaymentPart.objects.create(payment=payment, index=index, amount=part_amount)
    try:
        _open_part(payment.parts.order_by("index").first(), payment)
    except taps.TapsError as error:
        logger.warning("billing: create failed for payment %s: %s", payment.pk, error)
        Payment.objects.filter(pk=payment.pk).update(status=Payment.STATUS_CANCELLED, status_reason="create_failed")
        raise
    log_action(
        "billing.checkout_created",
        actor=user,
        organization=organization,
        target_type="payment",
        target_id=payment.pk,
        metadata={"months": months, "amount": amount, "method": method, "plan": plan.code, "parts": payment.parts.count()},
    )
    payment.refresh_from_db()
    return payment


def _apply(payment, now):
    """Mark paid and extend the subscription. The caller holds the payment row lock."""
    sub = subscription_for(payment.organization)
    sub = OrganizationSubscription.objects.select_for_update().get(pk=sub.pk)
    # Paid time is added on top of what is left, so paying early loses nothing.
    current_end = sub.current_period_end if sub.status in ("active", "past_due") else None
    trial_end = sub.trial_ends_at if sub.status == "trial" else None
    base = max([moment for moment in (now, current_end, trial_end) if moment])
    sub.plan = payment.plan
    sub.status = "active"
    sub.current_period_end = add_months(base, payment.months)
    sub.cancel_at_period_end = False
    sub.save()
    payment.status = Payment.STATUS_PAID
    payment.paid_at = now
    payment.period_end = sub.current_period_end
    payment.checkout_url = ""
    payment.save()
    log_action(
        "billing.payment_paid",
        organization=payment.organization,
        target_type="payment",
        target_id=payment.pk,
        metadata={"months": payment.months, "amount": payment.amount, "period_end": payment.period_end.isoformat()},
    )


def _part_paid(part):
    """Look at the current and any replaced donation of a part. Returns (paid, data_of_current)."""
    current = None
    for donation_id in [part.provider_payment_id, *part.meta.get("previous_ids", [])]:
        if not donation_id:
            continue
        data = taps.donation_status(donation_id)
        if current is None:
            current = data
        if taps.is_paid(data):
            if taps.paid_amount(data) >= part.amount:
                return True, data
            logger.warning("billing: part %s underpaid: %s", part.pk, data.get("amount"))
    return False, current or {}


def sync_payment(payment, now=None, renew=False):
    """Bring a pending payment up to date with Taps. Returns its status.

    `renew` (a user looking at the page) replaces an expired part link so a
    half-paid period can be finished; the background task never does that.
    """
    now = now or timezone.now()
    if payment.status != Payment.STATUS_PENDING:
        return payment.status
    with transaction.atomic():
        payment = Payment.objects.select_for_update().select_related("organization", "plan").get(pk=payment.pk)
        if payment.status != Payment.STATUS_PENDING:
            return payment.status
        while True:
            part = payment.parts.filter(status=Payment.STATUS_PENDING).order_by("index").first()
            if part is None:
                _apply(payment, now)
                return payment.status
            if not part.provider_payment_id:
                if renew or part.index > 1:
                    _open_part(part, payment)
                return payment.status
            paid, data = _part_paid(part)
            if paid:
                part.status = Payment.STATUS_PAID
                part.paid_at = now
                part.meta = {**part.meta, "status": data.get("status"), "paid_time": data.get("paidTime"), "paid_total": data.get("amount")}
                part.save()
                continue  # next part, or apply when none is left
            stale = taps.is_dead(data) or now - part.created_at > PENDING_TTL
            if not stale:
                return payment.status
            if not payment.parts.filter(status=Payment.STATUS_PAID).exists():
                reason = f"taps: {data.get('status')}" if taps.is_dead(data) else "expired"
                payment.status = Payment.STATUS_CANCELLED
                payment.status_reason = reason[:255]
                payment.checkout_url = ""
                payment.save()
                return payment.status
            # Part of the money is in: never cancel, offer a fresh link instead.
            if renew:
                _open_part(part, payment)
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
