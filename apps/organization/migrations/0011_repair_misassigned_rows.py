"""Return rows that 0005/0006 attached to the wrong library.

Those migrations put every row without an organization into the first library,
even when its book and reader belong to another one. A row is moved only when
both parents agree; anything ambiguous is left for a human to resolve.
"""
from django.db import migrations
from django.db.models import F, OuterRef, Subquery


def repair(apps, schema_editor):
    Book = apps.get_model("kitob", "Kitob")
    for app, name in (("navbat", "Navbat"), ("kitob", "BandQilish"), ("berish", "Berish")):
        Model = apps.get_model(app, name)
        Model.objects.filter(
            kitob__organization=F("oquvchi__organization")
        ).exclude(organization=F("kitob__organization")).update(
            organization=Subquery(
                Book.objects.filter(pk=OuterRef("kitob_id")).values("organization_id")[:1]
            )
        )
    Fine = apps.get_model("jarima", "Jarima")
    Loan = apps.get_model("berish", "Berish")
    Fine.objects.filter(berish__organization__isnull=False).exclude(
        organization=F("berish__organization")
    ).update(
        organization=Subquery(
            Loan.objects.filter(pk=OuterRef("berish_id")).values("organization_id")[:1]
        )
    )


class Migration(migrations.Migration):

    dependencies = [
        ("organization", "0010_merge_push_and_row_linking"),
        ("kitob", "0008_bandqilish_organization_kitob_organization_and_more"),
        ("oquvchi", "0010_ariza_organization_oquvchi_organization_and_more"),
        ("berish", "0009_berish_organization_berish_berish_org_holat_idx"),
        ("jarima", "0004_jarima_organization_jarima_jarima_org_tolandi_idx"),
        ("navbat", "0003_navbat_organization_navbat_navbat_org_holat_idx"),
    ]

    operations = [
        migrations.RunPython(repair, migrations.RunPython.noop),
    ]
