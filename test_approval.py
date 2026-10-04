import django
django.setup()
from oquvchi.models import Oquvchi
from kitob.models import Kitob, BandQilish
from berish.models import Berish
from kitob.services import band_qilish, band_qilishni_tasdiqla
from user.models import User

oquvchi = Oquvchi.objects.first()
xodim = User.objects.filter(rol='kutubxonachi').first()

# Find a book the user doesn't have
berilgan_kitob_ids = Berish.objects.filter(oquvchi=oquvchi, qaytarilgan_sana__isnull=True).values_list('kitob_id', flat=True)
kitob = Kitob.objects.exclude(id__in=berilgan_kitob_ids).first()

print(f"Testing approval flow:")
print(f"  Oquvchi: {oquvchi.fish}")
print(f"  Kitob: {kitob.nomi}")
print(f"  Xodim: {xodim.username}")

# Create hold
band, yangi = band_qilish(kitob, oquvchi, 'test approval')
print(f"\nHold created: ID={band.id}, Holati={band.holati}")

# Count before
berish_before = Berish.objects.count()

# Approve
band, berish = band_qilishni_tasdiqla(band, xodim, 'Tasdiqlandi')

print(f"\nAfter approval:")
print(f"  Band holati: {band.holati}")
print(f"  Berish created: {berish.id if berish else None}")
if berish:
    print(f"  Berish oquvchi: {berish.oquvchi.fish}")
    print(f"  Berish kitob: {berish.kitob.nomi}")

# Count after
berish_after = Berish.objects.count()
print(f"\nBerish count: before={Berish.objects.count() - (berish_after - berish_before) if False else 'N/A'}, after={berish_after}")