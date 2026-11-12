from django.db import models
from kitob.models import Kitob
from organization.models import TenantModel


class Nusxa(TenantModel):
    HOLAT_CHOICES = [
        ("mavjud", "Mavjud"),
        ("berilgan", "Berilgan"),
        ("band", "Band"),
        ("tamirda", "Ta'mirda"),
        ("yoqolgan", "Yo'qolgan"),
    ]
    kitob = models.ForeignKey(Kitob, on_delete = models.PROTECT, related_name="nusxalar")
    inventar_raqami = models.CharField(max_length = 30)
    holati = models.CharField(max_length=30, choices = HOLAT_CHOICES, default="mavjud")
    javon = models.CharField(max_length=30, blank=True)
    qabul_sana = models.DateField()
    izoh = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "inventar_raqami"],
                name="org_bitta_inventar",
            ),
        ]
        indexes = [
            models.Index(fields=["organization", "holati"], name="nusxa_org_holat_idx"),
        ]
