from django.db import migrations


def birinchi_kutubxonaga_bogla(apps, schema_editor):
    Organization = apps.get_model("organization", "Organization")
    Membership = apps.get_model("organization", "Membership")
    User = apps.get_model("user", "User")

    if Organization.objects.exists():
        return
    # Bo'sh bazada (yangi o'rnatish, test bazasi) kutubxona yaratilmaydi:
    # aks holda legacy rejim o'chib, global rollar ishlamay qoladi.
    if not User.objects.exists():
        return
    # Eski ma'lumotlar bitta kutubxonaga bog'lanadi (faqat ma'lumotlarni
    # saqlash maqsadida — tizim hech qachon barcha ma'lumotlarni bir
    # kutubxonaga majburan ko'chirmaydi, bu data migration shunchaki
    # mavjud bo'sh holatda ketma-ketlikni saqlashga yordam beradi)
    org = Organization.objects.create(
        nomi="Asosiy kutubxona",
        slug="asosiy-kutubxona",
    )
    for user in User.objects.filter(rol__in=["administrator", "kutubxonachi"], is_active=True):
        Membership.objects.get_or_create(
            organization=org,
            user=user,
            defaults={"rol": user.rol},
        )
        if not org.egasi and user.rol == "administrator":
            org.egasi = user
            org.save(update_fields=["egasi"])


def teskari(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("organization", "0002_organization_taklif_soat"),
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(birinchi_kutubxonaga_bogla, teskari),
    ]
