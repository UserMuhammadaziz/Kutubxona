from django.conf import settings
from django.db import transaction
from django.utils.timezone import localdate

from .models import Jarima


@transaction.atomic
def jarimani_hisobla(berish):
    """Bitta Berish uchun kechikish borligini tekshiradi va Jarima yozuvini
    update_or_create qiladi."""
    muddat = berish.qaytarish_muddati
    tekshiriladigan_sana = berish.qaytarilgan_sana or localdate()
    kechikkan = (tekshiriladigan_sana - muddat).days

    if kechikkan <= 0:
        mavjud = Jarima.objects.filter(berish=berish, tolandimi=False).first()
        if mavjud:
            mavjud.delete()
        return None

    mavjud = Jarima.objects.filter(berish=berish).first()
    if mavjud and mavjud.tolandimi:
        return mavjud

    org = berish.organization
    kunlik = org.kunlik_jarima if org else settings.KUNLIK_JARIMA
    jarima, _ = Jarima.objects.update_or_create(
        berish=berish,
        defaults={
            "organization": org,
            "kechikkan_kunlar": kechikkan,
            "kunlik_stavka": kunlik,
            "summa": kechikkan * kunlik,
        },
    )
    return jarima
