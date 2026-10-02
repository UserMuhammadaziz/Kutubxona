from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def kitobni_to_oldirish(apps, schema_editor):
    """`Berish.kitob` nusxa orqali berilgan eski yozuvlar uchun nusxaning
    kitobidan nusxalanadi. «Asli» berish (nusxa NULL) uchun alohida
    funksiya kerak emas — bunday yozuvlar hozircha yo'q."""
    Berish = apps.get_model("berish", "Berish")
    for berish in Berish.objects.filter(kitob__isnull=True, nusxa__isnull=False).iterator():
        berish.kitob_id = berish.nusxa.kitob_id
        berish.save(update_fields=["kitob"])


def kitobni_olish(apps, schema_editor):
    """Teskari migratsiya: `kitob` maydoni olib tashlanadi."""


class Migration(migrations.Migration):

    dependencies = [
        ("berish", "0003_alter_berish_holati_and_more"),
        ("kitob", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="berish",
            name="kitob",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="berishlar",
                to="kitob.kitob",
            ),
        ),
        migrations.AlterField(
            model_name="berish",
            name="nusxa",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="nusxa.nusxa",
            ),
        ),
        migrations.RunPython(kitobni_to_oldirish, kitobni_olish),
        migrations.AlterField(
            model_name="berish",
            name="kitob",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="berishlar",
                to="kitob.kitob",
            ),
        ),
        # Tizimning o'zi bergan «asli» kitobda kutubxonachi yo'q — shuning
        # uchun `bergan_xodim` bo'sh qoldiriladi.
        migrations.AlterField(
            model_name="berish",
            name="bergan_xodim",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="bergan_berishlar",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name="berish",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ("nusxa__isnull", True),
                    ("qaytarilgan_sana__isnull", True),
                ),
                fields=("kitob",),
                name="bitta_kitobda_bitta_faol_asli_berish",
            ),
        ),
    ]