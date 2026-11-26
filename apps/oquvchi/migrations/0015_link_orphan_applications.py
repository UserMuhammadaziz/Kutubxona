"""Link applications and readers that were saved without a library.

A row is linked only when its library is unambiguous: the applicant is already
a reader of exactly one library, or there is exactly one active library. Rows
that would break a unique constraint are left untouched; nothing is deleted or
rewritten.
"""
from django.db import migrations
from django.db.models import Case, IntegerField, Value, When


def link(apps, schema_editor):
    Application = apps.get_model("oquvchi", "Ariza")
    Reader = apps.get_model("oquvchi", "Oquvchi")
    Organization = apps.get_model("organization", "Organization")

    active = list(
        Organization.objects.filter(status="active").values_list("pk", flat=True)[:2]
    )
    only_active = active[0] if len(active) == 1 else None

    if only_active is not None:
        for reader in Reader.objects.filter(organization__isnull=True).order_by("pk"):
            peers = Reader.objects.filter(organization_id=only_active)
            taken = (
                peers.filter(telefon=reader.telefon).exists()
                or peers.filter(karta_raqami=reader.karta_raqami).exists()
                or (
                    reader.telegram_id is not None
                    and peers.filter(telegram_id=reader.telegram_id).exists()
                )
            )
            if not taken:
                Reader.objects.filter(pk=reader.pk).update(organization_id=only_active)

    # The pending application of an account wins, then the newest one.
    orphans = (
        Application.objects.filter(organization__isnull=True)
        .annotate(
            rank=Case(
                When(holati="kutmoqda", then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("rank", "-pk")
    )
    for application in orphans:
        libraries = set(
            Reader.objects.filter(
                telegram_id=application.telegram_id, organization__isnull=False
            ).values_list("organization_id", flat=True)
        )
        if len(libraries) == 1:
            target = libraries.pop()
        elif not libraries:
            target = only_active
        else:
            target = None
        if target is None:
            continue
        if not Application.objects.filter(
            organization_id=target, telegram_id=application.telegram_id
        ).exists():
            Application.objects.filter(pk=application.pk).update(organization_id=target)


class Migration(migrations.Migration):

    dependencies = [
        ("oquvchi", "0014_merge_subjects_and_application_format"),
        ("organization", "0011_repair_misassigned_rows"),
    ]

    operations = [migrations.RunPython(link, migrations.RunPython.noop)]
