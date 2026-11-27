from django.db import migrations

STANDARD = {
    "code": "standard",
    "nomi": "Standart",
    "tavsif": "Cheksiz xodim, kitob va kitobxon. To'lov oyma-oy, 1, 3, 6 yoki 12 oyga.",
    "narx_oylik": 60000,
    "max_staff": None,
    "max_resources": None,
    "max_customers": None,
    "tartib": 2,
    "faol": True,
}


def create_standard_plan(apps, schema_editor):
    Plan = apps.get_model("organization", "SubscriptionPlan")
    # Leave an existing paid plan alone: the platform may already have priced its own.
    if Plan.objects.filter(narx_oylik__gt=0).exists() or Plan.objects.filter(code=STANDARD["code"]).exists():
        return
    Plan.objects.create(**STANDARD)


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0001_initial"),
        ("organization", "0014_subscription_channel"),
    ]

    operations = [migrations.RunPython(create_standard_plan, migrations.RunPython.noop)]
