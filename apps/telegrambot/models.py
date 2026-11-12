import secrets

from django.db import models

from organization.models import Organization, TenantModel


class TelegramBot(models.Model):
    """Kutubxonaning shaxsiy Telegram boti.

    Token bazada faqat shifrlangan holda saqlanadi. Webhook manzili
    tasodifiy (opaque) bo'lib, kutubxona ID sini oshkor qilmaydi.
    """

    HOLAT_CHOICES = [
        ("ulanmoqda", "Ulanmoqda"),
        ("ulangan", "Ulangan"),
        ("uzilgan", "Uzilgan"),
        ("xato", "Xato"),
    ]

    organization = models.OneToOneField(
        Organization, on_delete=models.CASCADE, related_name="telegram_bot"
    )
    telegram_bot_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=64, blank=True)
    token_encrypted = models.TextField()
    webhook_path = models.CharField(max_length=80, unique=True)
    webhook_secret = models.CharField(max_length=80)
    holati = models.CharField(max_length=20, choices=HOLAT_CHOICES, default="ulanmoqda")
    webhook_ornatilgan = models.BooleanField(default=False)
    oxirgi_tekshiruv = models.DateTimeField(null=True, blank=True)
    oxirgi_xato = models.CharField(max_length=255, blank=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)
    yangilangan = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["organization__nomi"]
        verbose_name = "Telegram bot"
        verbose_name_plural = "Telegram botlar"

    def __str__(self):
        return f"@{self.username} — {self.organization.nomi}"

    @staticmethod
    def yangi_webhook_path():
        return secrets.token_urlsafe(32)

    @staticmethod
    def yangi_secret():
        return secrets.token_urlsafe(32)

    def set_token(self, token):
        from .encryption import shifrla

        self.token_encrypted = shifrla(token)

    def get_token(self):
        from .encryption import deshifrla

        return deshifrla(self.token_encrypted)


class TelegramSession(models.Model):
    """Botdagi suhbat holati (ariza, qidiruv, qaytarish)."""

    STEP_CHOICES = [
        ("ariza_fish", "Ariza: ism"),
        ("ariza_telefon", "Ariza: telefon"),
        ("ariza_sinf", "Ariza: sinf"),
        ("ariza_kasb", "Ariza: kasb"),
        ("qidiruv", "Qidiruv"),
        ("qaytarish", "Qaytarish"),
    ]

    bot = models.ForeignKey(
        TelegramBot, on_delete=models.CASCADE, related_name="sessiyalar"
    )
    telegram_id = models.BigIntegerField(db_index=True)
    chat_id = models.BigIntegerField()
    step = models.CharField(max_length=30, choices=STEP_CHOICES, blank=True)
    data = models.JSONField(default=dict, blank=True)
    yangilangan = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["bot", "telegram_id"], name="bot_bitta_sessiya"
            )
        ]

    def __str__(self):
        return f"{self.telegram_id} @ {self.bot.username} ({self.step})"


class TelegramUpdate(models.Model):
    """Webhook yangilanishlarini idempotent qayta ishlash uchun."""

    bot = models.ForeignKey(
        TelegramBot, on_delete=models.CASCADE, related_name="yangilanishlar"
    )
    update_id = models.BigIntegerField()
    qabul_qilindi = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["bot", "update_id"], name="bot_bitta_update"
            )
        ]
        indexes = [models.Index(fields=["bot", "update_id"], name="bot_update_idx")]


class KitobXabari(TenantModel):
    """Yangi kitob yoki kitob berilgani haqidagi ommaviy xabar.

    `kitob` + `tur` unique: Celery qayta ishga tushsa ham xabar ikki marta
    yuborilmaydi.
    """

    TUR_CHOICES = [
        ("yangi", "Yangi kitob"),
        ("berildi", "Kitob berildi"),
    ]

    kitob = models.ForeignKey(
        "kitob.Kitob", on_delete=models.CASCADE, related_name="xabarlar"
    )
    tur = models.CharField(max_length=20, choices=TUR_CHOICES)
    yuborildi = models.BooleanField(default=False)
    yuborilgan_soni = models.PositiveIntegerField(default=0)
    xato = models.CharField(max_length=255, blank=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)
    yuborilgan_sana = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["kitob", "tur"], name="kitob_bitta_xabar_turi"
            )
        ]
        indexes = [
            models.Index(fields=["organization", "yuborildi"], name="xabar_org_yubor_idx"),
        ]

    def __str__(self):
        return f"{self.kitob.nomi} — {self.get_tur_display()}"
