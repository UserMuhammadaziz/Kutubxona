"""0005 dan keyin bot tomonidan yaratilgan, tashkilotga bog'lanmagan qatorlar.

Bular ko'pincha o'qituvchilar: bot ularni yaratganda `organization` bo'sh
qolib, kutubxonachi ularni ro'yxatda ko'rmaydi va xabar yubora olmaydi.
Barcha bo'sh qatorlar birinchi (asosiy) tashkilotga bog'lanadi.

Ba'zi eski qatorlarda karta raqami / telefon raqami allaqachon shu
tashkilotdagi boshqa kitobxonga tegishli bo'lib qolgan (bot raqamlarni
tekshirmay yaratgan). Bunday qatorlarni o'chirmasdan, faqat noyob
identifikatorga ega qilib bog'laymiz — ma'lumot yo'qolmaydi.
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


def _noloyob_qilish(Model, row, org):
    """(organization, X) unique chegaralariga tushadigan maydonlarni tozalaydi."""
    for constraint in Model._meta.constraints:
        maydonlar = getattr(constraint, "fields", None)
        if not maydonlar or "organization" not in maydonlar:
            continue
        for nom in maydonlar:
            if nom == "organization":
                continue
            try:
                maydon = Model._meta.get_field(nom)
            except Exception:
                continue
            qiymat = getattr(row, nom, None)
            if qiymat in (None, ""):
                continue
            if isinstance(qiymat, str):
                yangi = qiymat
                n = 0
                while Model.objects.filter(organization=org, **{nom: yangi}).exists():
                    n += 1
                    if nom == "telefon":
                        # Telefon formati buzilmasligi uchun noyob, lekin
                        # to'g'ri ko'rinishdagi raqam yaratamiz.
                        yangi = (
                            f"+99890{row.pk:07d}"
                            if n == 1
                            else f"+99890{row.pk:05d}{n:02d}"
                        )
                        continue
                    qoshimcha = f"~{row.pk}" if n == 1 else f"~{row.pk}-{n}"
                    uzunlik = getattr(maydon, "max_length", None)
                    if uzunlik:
                        yangi = f"{qiymat[:max(0, uzunlik - len(qoshimcha))]}{qoshimcha}"
                    else:
                        yangi = f"{qiymat}{qoshimcha}"
                if yangi != qiymat:
                    setattr(row, nom, yangi)
            elif isinstance(qiymat, int) and getattr(maydon, "null", False):
                if Model.objects.filter(organization=org, **{nom: qiymat}).exists():
                    setattr(row, nom, None)


def bogla(apps, schema_editor):
    Organization = apps.get_model("organization", "Organization")
    org = Organization.objects.order_by("id").first()
    if org is None:
        return
    for ilova, model in MODELLAR:
        Model = apps.get_model(ilova, model)
        for row in Model.objects.filter(organization__isnull=True).order_by("pk"):
            _noloyob_qilish(Model, row, org)
            row.organization = org
            row.save()


class Migration(migrations.Migration):

    dependencies = [
        ("organization", "0005_eski_malumotlarni_bogla"),
    ]

    operations = [
        migrations.RunPython(bogla, migrations.RunPython.noop),
    ]
