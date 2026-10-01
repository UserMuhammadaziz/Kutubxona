from django.db import models
from berish.models import Berish
from user.models import User

class Jarima(models.Model):
    berish = models.OneToOneField(Berish, on_delete=models.CASCADE, related_name="jarima")
    kechikkan_kunlar = models.PositiveIntegerField()
    kunlik_stavka = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    summa = models.DecimalField(max_digits=12, decimal_places=2)
    tolandimi = models.BooleanField(default = False)
    tolangan_sana = models.DateTimeField(null = True, blank = True)
    qabul_qilgan = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT)
    eslatma_yuborilgan_sana = models.DateTimeField(null=True, blank=True)
    yangilangan = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["tolandimi", "eslatma_yuborilgan_sana"], name="jarima_eslatma_idx"),
        ]