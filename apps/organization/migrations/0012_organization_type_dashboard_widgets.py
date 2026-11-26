from django.db import migrations, models


def collapse_types(apps, schema_editor):
    """Only `library` and `school` remain.

    Until now the type was informational and every organization ran the school
    flow, so an organization whose readers already have a class or a teacher
    role is a school whatever it picked at sign-up. The rest become libraries.
    """
    Organization = apps.get_model("organization", "Organization")
    Oquvchi = apps.get_model("oquvchi", "Oquvchi")
    Ariza = apps.get_model("oquvchi", "Ariza")
    school_like = set()
    for model in (Oquvchi, Ariza):
        school_like.update(
            model.objects.filter(
                models.Q(rol="oqituvchi") | (models.Q(sinf__isnull=False) & ~models.Q(sinf=""))
            )
            .values_list("organization_id", flat=True)
            .distinct()
        )
    Organization.objects.filter(pk__in=school_like).update(type="school")
    Organization.objects.exclude(type__in=("library", "school")).update(type="library")


class Migration(migrations.Migration):
    dependencies = [
        ("organization", "0011_repair_misassigned_rows"),
        ("oquvchi", "0015_link_orphan_applications"),
    ]

    operations = [
        migrations.RenameField(model_name="organization", old_name="turi", new_name="type"),
        migrations.RunPython(collapse_types, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="organization",
            name="type",
            field=models.CharField(
                choices=[("library", "Kutubxona"), ("school", "Maktab")],
                default="school",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="organization",
            name="dashboard_widgets",
            field=models.JSONField(blank=True, default=None, null=True),
        ),
    ]
