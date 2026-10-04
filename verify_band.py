import django
django.setup()
from oquvchi.models import Oquvchi
from kitob.models import Kitob, BandQilish
from berish.models import Berish
from kitob.services import band_qilish

oquvchi = Oquvchi.objects.first()
berilgan_kitob_ids = Berish.objects.filter(oquvchi=oquvchi, qaytarilgan_sana__isnull=True).values_list('kitob_id', flat=True)
kitob = Kitob.objects.exclude(id__in=berilgan_kitob_ids).first()

print('Testing band_qilish with:')
print('  Oquvchi:', oquvchi.fish)
print('  Kitob:', kitob.nomi)

berish_before = Berish.objects.count()
band_before = BandQilish.objects.count()

band, yangi = band_qilish(kitob, oquvchi, 'test izoh')
print('Band created: ID=%s, Holati=%s, Yangi=%s' % (band.id, band.holati, yangi))

berish_after = Berish.objects.count()
band_after = BandQilish.objects.count()

print('Berish before:%s after:%s diff:%s' % (berish_before, berish_after, berish_after - berish_before))
print('Band before:%s after:%s diff:%s' % (band_before, band_after, band_after - band_before))
if berish_after > berish_before:
    print('ERROR: Berish was created!')
else:
    print('OK: No Berish created by band_qilish')