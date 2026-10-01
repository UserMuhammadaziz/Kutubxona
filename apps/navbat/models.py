from django.db import models
from django.db.models import Q
from kitob.models import Kitob 
from nusxa.models import Nusxa 
from oquvchi.models import Oquvchi 

class Navbat(models.Model):
    CHOICES_NAVBAT = [
    ("kutmoqda", "Kutmoqda"),
    ("taklif_qilindi", "Taklif qilindi"),
    ("yakunlandi", "Yakunlandi"),
    ("bekor", "Bekor"),
]

    CHOICES_JAVOB = [
    ("olaman", "Olaman"),
    ("kerak_emas", "Kerak emas"),
]

    kitob = models.ForeignKey(Kitob, on_delete=models.CASCADE, related_name="navbat")
    oquvchi = models.ForeignKey(Oquvchi, on_delete=models.CASCADE, related_name='navbatlar')
    navbat_sanasi = models.DateTimeField(auto_now_add=True)
    holati = models.CharField(max_length = 20, choices=CHOICES_NAVBAT, default="kutmoqda")
    ajratilgan_nusxa = models.ForeignKey(Nusxa, null = True, blank=True, on_delete=models.SET_NULL, related_name="navbatlar")
    taklif_vaqti = models.DateTimeField(null=True, blank=True)
    taklif_muddati = models.DateTimeField(null=True, blank=True)
    javob_vaqti = models.DateTimeField(null=True, blank=True)
    javob = models.CharField(max_length=20, choices=CHOICES_JAVOB, blank=True)
    taklif_xabari_yuborilgan = models.BooleanField(default=False)
    bekor_sababi = models.CharField(max_length=30, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["kitob", "oquvchi"], condition=Q(holati__in=["kutmoqda", "taklif_qilindi"]), name="unique_active_queue"),
            models.UniqueConstraint(fields=["kitob"], condition=Q(holati="taklif_qilindi"), name="one_pending_offer_per_book"),
        ]
        ordering = ["navbat_sanasi"]
        indexes = [
            models.Index(fields=["holati", "taklif_muddati"], name="navbat_taklif_muddat_idx"),
        ]