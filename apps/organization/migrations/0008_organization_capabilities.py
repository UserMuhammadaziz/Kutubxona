from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organization", "0007_heartbeat"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="capabilities",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
