from django.db import models
from user.models import User
from kitob.models import Kitob
from nusxa.models import Nusxa
from oquvchi.models import Oquvchi
from django.utils.timezone import now
from datetime import date
from django.conf import settings


class Berish(models.Model):
    CHOICES_HOLAT = [
    ("faol", "Faol"),
    ("qaytarilgan", "Qaytarilgan"),
    ("yoqolgan", "Yo'qolgan"),
]

    # Nusxa orqali beriladigan kitobda `nusxa` to'ladi. Nusxasi umuman yo'q
    # kitob esa «asli» holatda beriladi — u holda `nusxa` NULL qoladi va
    # kitob faqat `kitob` orqali bog'lanadi (nusxa yo'qligi ataylab
    # tekshiriladi, ilgari butunlay null edi).
    nusxa = models.ForeignKey(Nusxa, null=True, blank=True, on_delete=models.PROTECT)
    kitob = models.ForeignKey(Kitob, on_delete=models.PROTECT, related_name="berishlar")
    oquvchi = models.ForeignKey(Oquvchi, on_delete=models.PROTECT)
    bergan_xodim = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="bergan_berishlar")
    olgan_xodim = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name="olgan_berishlar")
    berilgan_sana = models.DateField(default=date.today)
    qaytarish_muddati = models.DateField()
    qaytarilgan_sana = models.DateField(null=True, blank=True)
    holati = models.CharField(max_length = 20, choices=CHOICES_HOLAT, default="faol")
    eslatma_yuborilgan = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["nusxa"],
                condition=models.Q(qaytarilgan_sana__isnull=True),
                name="bitta_nusxada_bitta_faol_berish",
            ),
            # «Asli» berish: nusxasi yo'q kitob faqat bitta faol berishga
            # ega bo'lishi mumkin (SQL da NULL qiymatlar o'zaro teng
            # hisoblanmagani uchun `nusxa` bo'yicha constraint ishlamaydi).
            models.UniqueConstraint(
                fields=["kitob"],
                condition=models.Q(
                    nusxa__isnull=True, qaytarilgan_sana__isnull=True
                ),
                name="bitta_kitobda_bitta_faol_asli_berish",
            ),
        ]
        indexes = [
            models.Index(fields=["oquvchi", "qaytarilgan_sana"], name="berish_oquvchi_qaytarilgan_idx"),
            models.Index(fields=["qaytarish_muddati"], name="berish_muddat_idx"),
        ]