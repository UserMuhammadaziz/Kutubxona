"""Traffic sources: landing visits and the source each signup came from."""
from django.db import models


class Visit(models.Model):
    """One browser session that opened a public page (landing, register)."""

    visitor_id = models.CharField(max_length=40, db_index=True)
    source = models.CharField(max_length=80, db_index=True)
    medium = models.CharField(max_length=80, blank=True)
    campaign = models.CharField(max_length=120, blank=True)
    term = models.CharField(max_length=120, blank=True)
    content = models.CharField(max_length=120, blank=True)
    referrer_host = models.CharField(max_length=120, blank=True)
    landing_path = models.CharField(max_length=200, blank=True)
    click_id = models.CharField(max_length=20, blank=True, help_text="gclid / fbclid / yclid")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Tashrif"
        verbose_name_plural = "Tashriflar"

    def __str__(self):
        return f"{self.source}/{self.medium or '-'} {self.created_at:%Y-%m-%d}"


class SignupAttribution(models.Model):
    """Where the owner of a registered organization came from.

    First touch is the earliest visit we know of for that browser, last touch
    is the visit just before the signup.
    """

    organization = models.OneToOneField(
        "organization.Organization", on_delete=models.CASCADE, related_name="attribution"
    )
    visitor_id = models.CharField(max_length=40, blank=True, db_index=True)
    source = models.CharField(max_length=80, db_index=True)
    medium = models.CharField(max_length=80, blank=True)
    campaign = models.CharField(max_length=120, blank=True)
    term = models.CharField(max_length=120, blank=True)
    content = models.CharField(max_length=120, blank=True)
    referrer_host = models.CharField(max_length=120, blank=True)
    landing_path = models.CharField(max_length=200, blank=True)
    click_id = models.CharField(max_length=20, blank=True)
    first_seen_at = models.DateTimeField(null=True, blank=True)
    last_source = models.CharField(max_length=80, blank=True)
    last_medium = models.CharField(max_length=80, blank=True)
    last_campaign = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ro'yxatdan o'tish manbasi"
        verbose_name_plural = "Ro'yxatdan o'tish manbalari"

    def __str__(self):
        return f"{self.organization} ← {self.source}/{self.medium or '-'}"
