from django.db import models
from django.core.validators import RegexValidator

class Oquvchi(models.Model):
    fish = models.CharField(max_length=130)
    telefon = models.CharField(
    max_length=20,
    unique=True,
    validators=[
        RegexValidator(
            regex=r'^\+998\d{9}$',
            message="Telefon +998123456789 formatida bo'lishi kerak."
        )
    ]
)
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    karta_raqami = models.CharField(max_length=20, unique=True)
    tugilgan_sana = models.DateField(null=True, blank=True)
    manzil = models.CharField(max_length=255, blank=True)
    royxat_sanasi = models.DateField(auto_now_add=True)
    faol = models.BooleanField(default=True)


class Ariza(models.Model):
    """Telegram bot orqali a'zolik arizasi. Kutubxonachi tasdiqlagach
    Oquvchi yaratiladi va telegram_id bog'lanadi."""

    HOLAT_CHOICES = [
        ("kutmoqda", "Kutmoqda"),
        ("tasdiqlandi", "Tasdiqlandi"),
        ("bekor", "Bekor"),
    ]

    telegram_id = models.BigIntegerField(unique=True)
    fish = models.CharField(max_length=130)
    telefon = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+998\d{9}$',
                message="Telefon +998123456789 formatida bo'lishi kerak."
            )
        ]
    )
    tugilgan_sana = models.DateField(null=True, blank=True)
    manzil = models.CharField(max_length=255, blank=True)
    holati = models.CharField(max_length=20, choices=HOLAT_CHOICES, default="kutmoqda")
    ariza_sanasi = models.DateTimeField(auto_now_add=True)
    tasdiqlangan_sana = models.DateTimeField(null=True, blank=True)
    izoh = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-ariza_sanasi"]