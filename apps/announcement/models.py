from django.conf import settings
from django.db import models

from organization.models import TenantModel


class Announcement(TenantModel):
    """A bulk Telegram message sent by a librarian to a group of readers."""

    AUDIENCE_CHOICES = [
        ("all", "All readers"),
        ("students", "Students"),
        ("teachers", "Teachers"),
        ("overdue", "Readers with overdue loans"),
        ("debtors", "Readers with unpaid fines"),
    ]

    text = models.TextField(max_length=1000)
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES)
    grade = models.CharField(max_length=30, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    recipients_count = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at", "-id"]
