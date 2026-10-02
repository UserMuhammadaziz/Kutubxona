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
    sinf = models.CharField(max_length=30, blank=True)
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

    ROL_CHOICES = [
        ("oquvchi", "Oquvchi"),
        ("oqituvchi", "O'qituvchi"),
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
    # null=True: eski arizalarda sinf yo'q (migratsiyadan oldin yuborilganlar).
    # Yangi arizalar uchun sinf majburiy — buni ArizaYaratishSerializer
    # validate_sinf() va blank=False orqali kafolatlaymiz.
    sinf = models.CharField(max_length=30, null=True)
    # O'qituvchilar uchun: o'qitayotgan fani (masalan "Matematika").
    # Oquvchi arizalarida bo'sh qoladi.
    kasb = models.CharField(max_length=60, blank=True)
    # Kim ariza yuborgani: oquvchi yoki o'qituvchi. Eski arizalar "oquvchi"
    # deb hisoblanadi (default qiymat).
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default="oquvchi")
    tugilgan_sana = models.DateField(null=True, blank=True)
    manzil = models.CharField(max_length=255, blank=True)
    holati = models.CharField(max_length=20, choices=HOLAT_CHOICES, default="kutmoqda")
    ariza_sanasi = models.DateTimeField(auto_now_add=True)
    tasdiqlangan_sana = models.DateTimeField(null=True, blank=True)
    izoh = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-ariza_sanasi"]
        indexes = [models.Index(fields=["holati", "-ariza_sanasi"], name="ariza_holati_sana_idx")]