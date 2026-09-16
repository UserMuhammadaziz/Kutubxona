from django.db import models
from kitob.models import Kitob

class Nusxa(models.Model):
    HOLAT_CHOICES = [
        ("mavjud", "Mavjud"),
        ("berilgan", "Berilgan"),
        ("band", "Band"),
        ("tamirda", "Ta'mirda"),
        ("yoqolgan", "Yo'qolgan"),
    ]
    kitob = models.ForeignKey(Kitob, on_delete = models.PROTECT, related_name="nusxalar")
    inventar_raqami = models.CharField(max_length = 30, unique = True)
    holati = models.CharField(max_length=30, choices = HOLAT_CHOICES, default="mavjud")
    javon = models.CharField(max_length=30, blank=True)
    qabul_sana = models.DateField()
    izoh = models.TextField(blank=True)
