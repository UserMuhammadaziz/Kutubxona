from django.db import models
from django.core.validators import RegexValidator

from organization.models import TenantModel


KASB_MAX_LENGTH = 200


def kasb_from_fans(fanlar):
    """Join subject names for the denormalised `kasb` column without exceeding its max_length.

    The M2M relation keeps the full list; `kasb` is only a display string, so it is cut at a
    name boundary and marked with an ellipsis instead of failing with DataError."""
    names = [f.nomi for f in fanlar]
    text = ", ".join(names)
    if len(text) <= KASB_MAX_LENGTH:
        return text
    kept = []
    for i, name in enumerate(names):
        # reserve room for the " +N" tail that reports how many names were cut
        if len(", ".join(kept + [name])) + len(f" +{len(names) - i}") > KASB_MAX_LENGTH:
            break
        kept.append(name)
    return ", ".join(kept) + f" +{len(names) - len(kept)}"


class Fan(models.Model):
    """O'qituvchi dars beradigan fan (oldindan ro'yxatga olingan).

    Hamma kutubxonalar uchun umumiy ro'yxat: o'qituvchi arizada shu
    ro'yxatdan tanlaydi. Yangi fanlarni platforma administratori
    Django admin orqali qo'shadi."""

    nomi = models.CharField(max_length=80, unique=True)
    faol = models.BooleanField(default=True)
    tartib = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ["tartib", "nomi"]
        verbose_name = "Fan"
        verbose_name_plural = "Fanlar"

    def __str__(self):
        return self.nomi


class Oquvchi(TenantModel):
    # O'quvchi yoki o'qituvchi. Ariza tasdiqlanganda arizadagi roldan olinadi
    # ("O'qituvchilar" bo'limi shu maydon orqali ajratiladi).
    rol = models.CharField(
        max_length=20,
        choices=[("oquvchi", "Oquvchi"), ("oqituvchi", "O'qituvchi")],
        default="oquvchi",
        db_index=True,
    )
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
    telegram_id = models.BigIntegerField(null=True, blank=True)
    karta_raqami = models.CharField(max_length=20)
    sinf = models.CharField(max_length=30, blank=True)
    # Faqat o'qituvchilar uchun: o'qitayotgan fani (arizadagi `kasb`).
    kasb = models.CharField(max_length=200, blank=True)
    fanlar = models.ManyToManyField(Fan, blank=True, related_name="oqituvchilar")
    tugilgan_sana = models.DateField(null=True, blank=True)
    manzil = models.CharField(max_length=255, blank=True)
    royxat_sanasi = models.DateField(auto_now_add=True)
    faol = models.BooleanField(default=True)
    # Eski (belgilanmagan) formatda ariza yuborganlar shu bayroq bilan
    # belgilanadi. Bot ularni /start da yangi formatda qayta ariza
    # topshirishga majbur qiladi. Tasdiqlanganda bayroq o'chiriladi.
    qayta_ariza_kerak = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "telefon"], name="org_bitta_telefon"
            ),
            models.UniqueConstraint(
                fields=["organization", "karta_raqami"], name="org_bitta_karta"
            ),
            models.UniqueConstraint(
                fields=["organization", "telegram_id"],
                condition=models.Q(telegram_id__isnull=False),
                name="org_bitta_oquvchi_telegram",
            ),
        ]
        indexes = [
            models.Index(fields=["organization", "rol", "faol"], name="oquvchi_org_rol_idx"),
        ]


class Ariza(TenantModel):
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

    telegram_id = models.BigIntegerField()
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
    kasb = models.CharField(max_length=200, blank=True)
    fanlar = models.ManyToManyField(Fan, blank=True, related_name="ariza_oqituvchilari")
    # Kim ariza yuborgani: oquvchi yoki o'qituvchi. Eski arizalar "oquvchi"
    # deb hisoblanadi (default qiymat).
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default="oquvchi")
    tugilgan_sana = models.DateField(null=True, blank=True)
    manzil = models.CharField(max_length=255, blank=True)
    holati = models.CharField(max_length=20, choices=HOLAT_CHOICES, default="kutmoqda")
    ariza_sanasi = models.DateTimeField(auto_now_add=True)
    tasdiqlangan_sana = models.DateTimeField(null=True, blank=True)
    izoh = models.CharField(max_length=255, blank=True)
    # Eski formatda yuborilgan arizalar bot tomonidan qayta yuborilishi shart.
    qayta_ariza_kerak = models.BooleanField(default=False)

    class Meta:
        ordering = ["-ariza_sanasi"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "telegram_id"],
                name="org_bitta_ariza_telegram",
            ),
        ]
        indexes = [
            models.Index(fields=["holati", "-ariza_sanasi"], name="ariza_holati_sana_idx"),
            models.Index(fields=["organization", "holati"], name="ariza_org_holat_idx"),
        ]