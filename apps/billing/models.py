from django.conf import settings
from django.db import models

from organization.models import Organization, SubscriptionPlan


class Payment(models.Model):
    """One subscription purchase: a library pays for `months` of a plan."""

    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Kutilmoqda"),
        (STATUS_PAID, "To'langan"),
        (STATUS_CANCELLED, "Bekor qilingan"),
    ]
    PROVIDER_TAPS = "taps"
    PROVIDER_CHOICES = [(PROVIDER_TAPS, "Taps")]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="payments")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="payments")
    months = models.PositiveSmallIntegerField()
    amount = models.PositiveIntegerField(help_text="So'm, komissiyasiz")
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default=PROVIDER_TAPS)
    method = models.CharField(max_length=30)
    provider_payment_id = models.CharField(max_length=64, blank=True, db_index=True)
    checkout_url = models.URLField(max_length=1000, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    status_reason = models.CharField(max_length=255, blank=True)
    meta = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True, help_text="Obuna shu to'lovdan keyin tugaydigan sana")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"

    def __str__(self):
        return f"{self.organization} — {self.months} oy, {self.amount} so'm ({self.status})"


class PaymentPart(models.Model):
    """Taps caps one donation (200 000 so'm), so a long period is paid in equal parts."""

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="parts")
    index = models.PositiveSmallIntegerField()
    amount = models.PositiveIntegerField()
    provider_payment_id = models.CharField(max_length=64, blank=True, db_index=True)
    checkout_url = models.URLField(max_length=1000, blank=True)
    status = models.CharField(max_length=20, choices=Payment.STATUS_CHOICES, default=Payment.STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["payment", "index"]
        constraints = [models.UniqueConstraint(fields=["payment", "index"], name="billing_part_unique_index")]

    def __str__(self):
        return f"{self.payment_id}#{self.index}: {self.amount} ({self.status})"
