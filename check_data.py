import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from oquvchi.models import Oquvchi
from kitob.models import Kitob
from berish.models import Berish

print('Oquvchilar:')
for o in Oquvchi.objects.all():
    print(f'  {o.id}: {o.fish} (rol={o.rol})')

print('\nKitoblar:')
for k in Kitob.objects.all():
    mavjud = k.nusxalar.filter(holati='mavjud').count()
    print(f'  {k.id}: {k.nomi} (mavjud_nusxalar={mavjud})')

print('\nBerishlar:')
for b in Berish.objects.filter(qaytarilgan_sana__isnull=True):
    print(f'  {b.id}: kitob={b.kitob_nomi}, oquvchi={b.oquvchi.fish}')