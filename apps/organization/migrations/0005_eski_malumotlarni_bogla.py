from django.db import migrations

# (ilova, model) — organization maydoni NULL bo'lgan eski qatorlar.
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


def eski_malumotlarni_bogla(apps, schema_editor):
    """0003 faqat tashkilot va a'zoliklarni yaratadi, mavjud qatorlarni esa
    bog'lamaydi — natijada tenant filtri hammasini yashirib qo'yadi.
    Organization'siz qolgan qatorlar birinchi (asosiy) tashkilotga bog'lanadi."""
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
        ("organization", "0004_auditlog_organizationsubscription_subscriptionplan_and_more"),
        ("kitob", "0008_bandqilish_organization_kitob_organization_and_more"),
        ("nusxa", "0002_nusxa_organization_alter_nusxa_inventar_raqami_and_more"),
        ("oquvchi", "0010_ariza_organization_oquvchi_organization_and_more"),
        ("berish", "0009_berish_organization_berish_berish_org_holat_idx"),
        ("jarima", "0004_jarima_organization_jarima_jarima_org_tolandi_idx"),
        ("navbat", "0003_navbat_organization_navbat_navbat_org_holat_idx"),
    ]

    operations = [
        migrations.RunPython(eski_malumotlarni_bogla, migrations.RunPython.noop),
    ]
