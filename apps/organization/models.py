import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    """Mustaqil kutubxona (tenant).

    Har bir kitob, nusxa, o'quvchi, berish, jarima, navbat va telegram bot
    aynan bitta kutubxonaga tegishli. Boshqa kutubxona ma'lumotlari hech
    qachon ko'rinmaydi.
    """

    HOLAT_PENDING = "pending"
    HOLAT_ACTIVE = "active"
    HOLAT_REJECTED = "rejected"
    HOLAT_SUSPENDED = "suspended"
    HOLAT_ARCHIVED = "archived"
    HOLAT_CHOICES = [
        (HOLAT_PENDING, "Kutilmoqda"),
        (HOLAT_ACTIVE, "Faol"),
        (HOLAT_REJECTED, "Rad etilgan"),
        (HOLAT_SUSPENDED, "To'xtatilgan"),
        (HOLAT_ARCHIVED, "Arxivlangan"),
    ]
    # Faol bo'lmagan holatlar: tashkilot ma'lumotlariga kirish yopiladi.
    FAOL_EMAS_HOLATLAR = (HOLAT_PENDING, HOLAT_REJECTED, HOLAT_SUSPENDED, HOLAT_ARCHIVED)

    TURI_CHOICES = [
        ("library", "Kutubxona"),
        ("school", "Maktab / ta'lim muassasasi"),
        ("university", "Universitet / kollej"),
        ("office", "Ofis / tashkilot"),
        ("other", "Boshqa"),
    ]

    nomi = models.CharField(max_length=160)
    slug = models.SlugField(max_length=80, unique=True)
    turi = models.CharField(max_length=20, choices=TURI_CHOICES, default="library")
    tavsif = models.TextField(blank=True)
    telefon = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    manzil = models.CharField(max_length=255, blank=True)
    logo_url = models.URLField(max_length=500, blank=True)
    # `faol` eski API va botlar bilan moslik uchun saqlanadi. Yangi kod
    # `status` dan foydalanadi; `status` o'zgarganda `faol` avtomatik
    # sinxronlanadi (pastdagi `save`).
    faol = models.BooleanField(default=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=HOLAT_CHOICES,
        default=HOLAT_ACTIVE,
        db_index=True,
    )
    status_reason = models.TextField(blank=True)
    status_changed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasdiqlagan_tashkilotlar",
    )
    egasi = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="egalik_qilgan_kutubxonalar",
    )

    muddat_kun = models.PositiveIntegerField(default=14)
    kunlik_jarima = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    limit_kitob = models.PositiveIntegerField(default=3)
    taklif_soat = models.PositiveIntegerField(default=24)
    eslatma_kunlar_oldin = models.PositiveIntegerField(default=2)
    kitob_xabarlari_yoqilgan = models.BooleanField(default=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)
    yangilangan = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nomi"]
        verbose_name = "Kutubxona"
        verbose_name_plural = "Kutubxonalar"
        indexes = [
            models.Index(fields=["status", "faol"], name="org_status_faol_idx"),
        ]

    def __str__(self):
        return self.nomi

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._yangi_slug()
        # `faol` va `status` hech qachon bir-biriga zid bo'lmasin.
        self.faol = self.status == self.HOLAT_ACTIVE
        super().save(*args, **kwargs)

    @property
    def faolmi(self):
        """Tashkilot ma'lumotlariga kirish ochiqmi."""
        return self.status == self.HOLAT_ACTIVE and self.faol

    @staticmethod
    def _yangi_slug():
        return f"kutubxona-{uuid.uuid4().hex[:10]}"


class Membership(models.Model):
    """Foydalanuvchining kutubxonadagi roli.

    Bitta foydalanuvchi bir nechta kutubxonada turli rolga ega bo'lishi
    mumkin. Kutubxonaga tegishli barcha ruxsatlar shu yozuv orqali
    tekshiriladi.
    """

    ROL_CHOICES = [
        ("egasi", "Egasi"),
        ("administrator", "Administrator"),
        ("kutubxonachi", "Kutubxonachi"),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="a_zolar"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="a_zoliklar"
    )
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default="kutubxonachi")
    faol = models.BooleanField(default=True)
    telegram_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    link_code = models.CharField(max_length=64, blank=True)
    link_code_expires = models.DateTimeField(null=True, blank=True)
    qoshilgan = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["organization__nomi", "user__full_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"], name="org_bitta_azolik"
            ),
            models.UniqueConstraint(
                fields=["organization", "telegram_id"],
                condition=models.Q(telegram_id__isnull=False),
                name="org_bitta_telegram",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "faol"], name="azolik_user_faol_idx"),
        ]

    def __str__(self):
        return f"{self.user} — {self.organization} ({self.get_rol_display()})"

    @property
    def xodimmi(self):
        return self.rol in ("egasi", "administrator", "kutubxonachi")

    @property
    def adminmi(self):
        return self.rol in ("egasi", "administrator")

    def yangi_link_kod(self):
        self.link_code = secrets.token_urlsafe(24)
        self.link_code_expires = timezone.now() + timedelta(minutes=15)
        self.save(update_fields=["link_code", "link_code_expires"])
        return self.link_code


class TenantModel(models.Model):
    """Barcha kutubxona ma'lumotlari uchun abstract asos.

    `null=True` faqat eski ma'lumotlarni migratsiya qilish va testlarni
    bosqichma-bosqich ko'chirish uchun. Yangi yozuvlar har doim aniq
    kutubxona bilan yaratilishi shart — buni view/serializer qatlami
    ta'minlaydi.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
        related_name="+",
    )

    class Meta:
        abstract = True


class SubscriptionPlan(models.Model):
    """SaaS tarif rejasi.

    Limitlar `None` bo'lsa — cheksiz. Narx hozircha faqat ma'lumot sifatida
    saqlanadi; real to'lov integratsiyasi alohida bosqichda qo'shiladi.
    """

    code = models.SlugField(max_length=40, unique=True)
    nomi = models.CharField(max_length=80)
    tavsif = models.TextField(blank=True)
    narx_oylik = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_staff = models.PositiveIntegerField(null=True, blank=True)
    max_resources = models.PositiveIntegerField(null=True, blank=True)
    max_customers = models.PositiveIntegerField(null=True, blank=True)
    xususiyatlar = models.JSONField(default=dict, blank=True)
    tartib = models.PositiveSmallIntegerField(default=0)
    faol = models.BooleanField(default=True)

    class Meta:
        ordering = ["tartib", "narx_oylik", "nomi"]
        verbose_name = "Tarif rejasi"
        verbose_name_plural = "Tarif rejalari"

    def __str__(self):
        return self.nomi


class OrganizationSubscription(models.Model):
    """Tashkilotning tarif rejasi va trial/amal qilish holati."""

    HOLAT_CHOICES = [
        ("trial", "Sinov muddati"),
        ("active", "Faol"),
        ("past_due", "To'lov kechikkan"),
        ("canceled", "Bekor qilingan"),
        ("expired", "Muddati tugagan"),
    ]

    organization = models.OneToOneField(
        Organization, on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.PROTECT, related_name="obunalar"
    )
    status = models.CharField(max_length=20, choices=HOLAT_CHOICES, default="trial")
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    yaratilgan = models.DateTimeField(auto_now_add=True)
    yangilangan = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tashkilot obunasi"
        verbose_name_plural = "Tashkilot obunalari"
        indexes = [
            models.Index(fields=["status", "current_period_end"], name="obuna_holat_idx"),
        ]

    def __str__(self):
        return f"{self.organization} — {self.plan} ({self.get_status_display()})"

    @property
    def muddati_otganmi(self):
        now = timezone.now()
        if self.status == "trial" and self.trial_ends_at:
            return self.trial_ends_at < now
        if self.current_period_end:
            return self.current_period_end < now
        return False

    @property
    def samarali_holat(self):
        if self.muddati_otganmi and self.status in ("trial", "active", "past_due"):
            return "expired"
        return self.status

    @property
    def faolmi(self):
        return self.samarali_holat in ("trial", "active")


class AuditLog(models.Model):
    """Platforma va tashkilot darajasidagi muhim amallar tarixi."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_loglar",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_loglar",
    )
    action = models.CharField(max_length=80, db_index=True)
    target_type = models.CharField(max_length=80, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    yaratilgan = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-yaratilgan", "-id"]
        verbose_name = "Audit yozuvi"
        verbose_name_plural = "Audit yozuvlari"
        indexes = [
            models.Index(fields=["organization", "-yaratilgan"], name="audit_org_vaqt_idx"),
            models.Index(fields=["action", "-yaratilgan"], name="audit_action_vaqt_idx"),
        ]

    def __str__(self):
        return f"{self.action} — {self.organization or 'platforma'}"
