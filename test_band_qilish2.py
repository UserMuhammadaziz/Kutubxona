import django
django.setup()
from oquvchi.models import Oquvchi
from kitob.models import Kitob, BandQilish
from berish.models import Berish
from kitob.services import band_qilish

oquvchi = Oquvchi.objects.first()

# Find a book the user doesn't have
berilgan_kitob_ids = Berish.objects.filter(oquvchi=oquvchi, qaytarilgan_sana__isnull=True).values_list('kitob_id', flat=True)
kitob = Kitob.objects.exclude(id__in=berilgan_kitob_ids).first()

if not kitob:
    print("User has all books!")
    exit(1)

print("Testing band_qilish with:")
print("  Oquvchi:", oquvchi.fish)
print("  Kitob:", kitob.nomi)

# Count before
berish_before = Berish.objects.count()
band_before = BandQilish.objects.count()

# Create hold
band, yangi = band_qilish(kitob, oquvchi, 'test izoh')
print("Band created:")
print("  ID:", band.id)
print("  Holati:", band.holati)
print("  Yangi:", yangi)

# Count after
berish_after = Berish.objects.count()
band_after = BandQilish.objects.count()

print("\nResults:")
print("  Berish before:", berish_before, "after:", berish_after, "diff:", berish_after - berish_before)
print("  Band before:", band_before, "after:", band_after, "diff:", band_after - band_before)

if berish_after > berish_before:
    print("ERROR: Berish was created! Should not happen.")
else:
    print("OK: No Berish created by band_qilish")