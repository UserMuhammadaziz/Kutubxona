import django
django.setup()
from oquvchi.models import Oquvchi
from kitob.models import Kitob
from berish.models import Berish

print("Oquvchilar:")
for o in Oquvchi.objects.all():
    print("  ID:", o.id, "Fish:", o.fish.encode('ascii', 'ignore').decode(), "Rol:", o.rol)

print("\nKitoblar:")
for k in Kitob.objects.all():
    mavjud = k.nusxalar.filter(holati="mavjud").count()
    print("  ID:", k.id, "Nomi:", k.nomi.encode('ascii', 'ignore').decode(), "Mavjud:", mavjud)

print("\nBerishlar:")
for b in Berish.objects.filter(qaytarilgan_sana__isnull=True):
    print("  ID:", b.id, "Kitob:", b.kitob_nomi.encode('ascii', 'ignore').decode(), "Oquvchi:", b.oquvchi.fish.encode('ascii', 'ignore').decode())