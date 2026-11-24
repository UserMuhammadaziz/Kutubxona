from django.db import models
from django.contrib.auth.models import AbstractUser 


class User(AbstractUser):
    ROLE_CHOICES = [
    ("kutubxonachi", "Kutubxonachi"),
    ("administrator", "Administrator"),
]
    username = models.CharField(max_length = 150, unique=True)
    full_name = models.CharField(max_length = 120)
    rol = models.CharField(max_length = 20, choices=ROLE_CHOICES, default="kutubxonachi")
    telefon = models.CharField(max_length = 20, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.full_name
    


class ChatXabar(models.Model):
    """AI yordamchi (Chatbot) suhbati: har foydalanuvchi uchun alohida saqlanadi."""

    ROLLAR = [("user", "Foydalanuvchi"), ("model", "AI")]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_xabarlari"
    )
    rol = models.CharField(max_length=5, choices=ROLLAR)
    matn = models.TextField()
    yaratilgan = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        indexes = [models.Index(fields=["user", "id"], name="chat_user_id_idx")]

    def __str__(self):
        return f"{self.user_id} {self.rol}: {self.matn[:40]}"


class XatolikXabari(models.Model):
    """Profil orqali kelgan xatolik xabari (qo'lda yoki avtomatik ushlangan).

    Xabar bazada saqlanadi (keyin ko'rish/tekshirish uchun) va joriy
    kutubxonaning egasi/administratorlariga Telegram orqali yuboriladi.
    """

    TURLARI = [
        ("qolda", "Qo'lda yuborilgan"),
        ("avtomatik", "Avtomatik ushlangan"),
    ]

    organization = models.ForeignKey(
        "organization.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="xatolik_xabarlari",
    )
    yuborgan = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="xatolik_xabarlari",
    )
    matn = models.TextField()
    sahifa = models.CharField(max_length=300, blank=True)
    tur = models.CharField(max_length=20, choices=TURLARI, default="qolda")
    yaratilgan = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-yaratilgan"]
        indexes = [
            models.Index(
                fields=["organization", "-yaratilgan"], name="xato_org_sana_idx"
            )
        ]

    def __str__(self):
        return f"{self.yaratilgan:%Y-%m-%d %H:%M} — {self.matn[:50]}"
