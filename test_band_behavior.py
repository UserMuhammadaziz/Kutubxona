import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from kitob.models import BandQilish, Kitob
from berish.models import Berish
from oquvchi.models import Oquvchi
from kitob.services import band_qilish

# Test: create a hold and verify no Berish is created
kitob = Kitob.objects.first()
oquvchi = Oquvchi.objects.first()
print(f'Testing with kitob={kitob.nomi}, oquvchi={oquvchi.fish}')

# Count before
berish_before = Berish.objects.count()
band_before = BandQilish.objects.count()

# Create hold
band, yangi = band_qilish(kitob, oquvchi, 'test izoh')
print(f'Band created: id={band.id}, holati={band.holati}, yangi={yangi}')

# Count after
berish_after = Berish.objects.count()
band_after = BandQilish.objects.count()

print(f'Berish before: {berish_before}, after: {berish_after}')
print(f'Band before: {band_before}, after: {band_after}')
print(f'Berish created by band_qilish: {berish_after - berish_before}')

# Now test approve
if band.holati == 'kutmoqda':
    from kitob.services import band_qilishni_tasdiqla
    from user.models import User
    xodim = User.objects.filter(rol='kutubxonachi').first()
    print(f'\nApproving with xodim={xodim.username}')
    band, berish = band_qilishni_tasdiqla(band, xodim, 'Tasdiqlandi')
    print(f'After approve: band.holati={band.holati}, berish={berish.id if berish else None}')
    print(f'Berish count: {Berish.objects.count()}')