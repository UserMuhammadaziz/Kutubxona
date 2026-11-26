from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("telegrambot", "0003_application_library_steps"),
    ]

    operations = [
        migrations.AddField(
            model_name="telegrambot",
            name="polling",
            field=models.BooleanField(default=False),
        ),
    ]
