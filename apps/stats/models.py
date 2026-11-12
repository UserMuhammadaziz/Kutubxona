from django.conf import settings
from django.db import models

from organization.models import Organization


class LibraryRating(models.Model):
    """Kutubxona reytingi — kitobxonlar baholaydi."""

    STARS = [(i, f"{i} yulduz") for i in range(1, 6)]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="reytinglar"
    )
    oquvchi = models.ForeignKey(
        "oquvchi.Oquvchi", on_delete=models.CASCADE, related_name="kutubxona_reytinglari"
    )
    baho = models.PositiveSmallIntegerField(choices=STARS)
    izoh = models.CharField(max_length=255, blank=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)
    yangilangan = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "oquvchi"], name="bitta_reyting_har_ku"
            )
        ]
        ordering = ["-yangilangan"]
        indexes = [
            models.Index(fields=["organization", "-baho"], name="reyting_org_baho_idx"),
        ]

    def __str__(self):
        return f"{self.organization.nomi} — {self.oquvchi.fish}: {self.baho}"


class LibraryActivityRating(models.Model):
    """Kutubxonaning faollik reytingi.

    O'quvchilar, sinflar, o'qituvchilar va umumiy faollik bo'yicha
    hisoblanuvchi ballar — kutubxonalar o'rtasida bellashuv uchun.
    """

    organization = models.OneToOneField(
        Organization, on_delete=models.CASCADE, related_name="faollik_reytingi"
    )
    oquvchi_bali = models.FloatField(default=0)
    sinf_bali = models.FloatField(default=0)
    oqituvchi_bali = models.FloatField(default=0)
    umumiy_bali = models.FloatField(default=0)
    oquvchi_soni = models.PositiveIntegerField(default=0)
    faol_oquvchi_soni = models.PositiveIntegerField(default=0)
    berishlar_soni = models.PositiveIntegerField(default=0)
    qaytarilgan_soni = models.PositiveIntegerField(default=0)
    yangilangan = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-umumiy_bali"]

    def __str__(self):
        return f"{self.organization.nomi}: {self.umumiy_bali}"
