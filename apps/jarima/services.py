from django.conf import settings
from django.db import transaction
from django.utils.timezone import localdate

from .models import Jarima


@transaction.atomic
def jarimani_hisobla(berish):
    """Bitta Berish uchun kechikish borligini tekshiradi va Jarima yozuvini
    update_or_create qiladi. OneToOne maydon + shu funksiya orqali ikki
    qavatli himoya — bitta berishga ikkinchi marta jarima yozilmaydi.
    Allaqachon to'langan jarimaga tegilmaydi. Idempotent: bir necha marta
    ketma-ket chaqirilsa ham natija o'zgarmaydi.

    Kechikish qolmagan holat (`kechikkan <= 0`) uchun avval yaratilgan va
    hali to'lanmagan jarima o'chiriladi — aks holda masalan muddat keyin
    uzaytirilganda yoki qaytarish sanasi aniq belgilanganda o'quvchi
    to'lanmagan, amaliyotda mavjud bo'lmagan jarimani ko'radi."""
    muddat = berish.qaytarish_muddati
    # `date.today()` serverining mahalliy vaqtini ishlatadi va TZ da
    # farq bo'lsa (masalda server UTC da ishlaydi) kechikish bir kun
    # noto'g'ri hisoblanadi — `localdate()` Django sozlamasidan oladi.
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

    jarima, _ = Jarima.objects.update_or_create(
        berish=berish,
        defaults={
            "kechikkan_kunlar": kechikkan,
            "kunlik_stavka": settings.KUNLIK_JARIMA,
            "summa": kechikkan * settings.KUNLIK_JARIMA,
        },
    )
    return jarima
