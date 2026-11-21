"""0005 dan keyin bot tomonidan yaratilgan, tashkilotga bog'lanmagan qatorlar.

Bular ko'pincha o'qituvchilar: bot ularni yaratganda `organization` bo'sh
qolib, kutubxonachi ularni ro'yxatda ko'rmaydi va xabar yubora olmaydi.
Barcha bo'sh qatorlar birinchi (asosiy) tashkilotga bog'lanadi.
"""
from django.db import migrations

MODELLAR = [
    ("kitob", "Kitob"),
    ("kitob", "BandQilish"),
    ("nusxa", "Nusxa"),
    ("oquvchi", "Oquvchi"),
    ("oquvchi", "Ariza"),
    ("berish", "Berish"),
    ("jarima", "Jarima"),
    ("navbat", "Navbat"),
]


def bogla(apps, schema_editor):
    Organization = apps.get_model("organization", "Organization")
    org = Organization.objects.order_by("id").first()
    if org is None:
        return
    for ilova, model in MODELLAR:
        apps.get_model(ilova, model).objects.filter(organization__isnull=True).update(
            organization=org
        )


class Migration(migrations.Migration):

    dependencies = [
        ("organization", "0005_eski_malumotlarni_bogla"),
    ]

    operations = [
        migrations.RunPython(bogla, migrations.RunPython.noop),
    ]
