from django.db import migrations

FANLAR = [
    "Ona tili",
    "Adabiyot",
    "Matematika",
    "Algebra",
    "Geometriya",
    "Fizika",
    "Kimyo",
    "Biologiya",
    "Tarix",
    "Geografiya",
    "Informatika",
    "Ingliz tili",
    "Rus tili",
    "Nemis tili",
    "Fransuz tili",
    "Arab tili",
    "Jismoniy tarbiya",
    "Tasviriy san'at",
    "Musiqa",
    "Texnologiya (mehnat)",
    "Chizmachilik",
    "Huquq",
    "Iqtisodiyot",
    "Tarbiya",
    "Boshlang'ich ta'lim",
    "Boshqa",
]


def yukla(apps, schema_editor):
    Fan = apps.get_model("oquvchi", "Fan")
    for i, nomi in enumerate(FANLAR, start=1):
        Fan.objects.get_or_create(nomi=nomi, defaults={"tartib": i * 10})
    # "Boshqa" doim ro'yxat oxirida
    Fan.objects.filter(nomi="Boshqa").update(tartib=10000)


class Migration(migrations.Migration):
    dependencies = [("oquvchi", "0011_fan_va_fanlar")]
    operations = [migrations.RunPython(yukla, migrations.RunPython.noop)]
