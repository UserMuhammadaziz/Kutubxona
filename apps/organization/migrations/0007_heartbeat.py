from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organization", "0006_pushsubscription"),
    ]

    operations = [
        migrations.CreateModel(
            name="Heartbeat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=40, unique=True)),
                ("last_seen", models.DateTimeField()),
                ("detail", models.JSONField(blank=True, default=dict)),
            ],
        ),
    ]
