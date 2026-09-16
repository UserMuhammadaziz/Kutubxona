from datetime import date

from django.conf import settings
from django.db import transaction

from .models import Jarima


@transaction.atomic
def jarimani_hisobla(berish):
    """Bitta Berish uchun kechikish borligini tekshiradi va Jarima yozuvini
    update_or_create qiladi. OneToOne maydon + shu funksiya orqali ikki
    qavatli himoya — bitta berishga ikkinchi marta jarima yozilmaydi.
    Allaqachon to'langan jarimaga tegilmaydi. Idempotent: bir necha marta
    ketma-ket chaqirilsa ham natija o'zgarmaydi."""
    muddat = berish.qaytarish_muddati
    tekshiriladigan_sana = berish.qaytarilgan_sana or date.today()
    kechikkan = (tekshiriladigan_sana - muddat).days

    if kechikkan <= 0:
        return None

    mavjud = Jarima.objects.filter(berish=berish).first()
    if mavjud and mavjud.tolandimi:
        return mavjud

    jarima, _ = Jarima.objects.update_or_create(
        berish=berish,
        defaults={
            "kechikkan_kunlar": kechikkan,
            "kunlik_stavka": settings.KUNLIK_JARIMA,
            "summa": kechikkan * settings.KUNLIK_JARIMA,
        },
    )
    return jarima
