import django
django.setup()
from oquvchi.models import Oquvchi
from kitob.models import Kitob, BandQilish
from berish.models import Berish
from rest_framework.test import APIClient

# Setup
oquvchi = Oquvchi.objects.first()
kitob = Kitob.objects.exclude(id__in=Berish.objects.filter(oquvchi=oquvchi, qaytarilgan_sana__isnull=True).values_list('kitob_id', flat=True)).first()

print(f"Testing API POST /holds/ with:")
print(f"  Oquvchi: {oquvchi.fish} (telegram_id={oquvchi.telegram_id})")
print(f"  Kitob: {kitob.nomi} (id={kitob.id})")

client = APIClient()
response = client.post(
    '/api/holds/',
    {'kitob': kitob.id, 'telegram_id': oquvchi.telegram_id, 'izoh': 'test from api'},
    format='json'
)

print(f"\nResponse status: {response.status_code}")
print(f"Response content: {response.content.decode()}")

if response.status_code == 201:
    band = BandQilish.objects.get(id=response.data['id'])
    print(f"\nBand created:")
    print(f"  ID: {band.id}")
    print(f"  Holati: {band.holati}")
    print(f"  Berish: {band.berish}")
    
    # Check if Berish was created
    berish_count = Berish.objects.count()
    print(f"\nTotal Berish count: {berish_count}")