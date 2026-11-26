import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organization", "0008_organization_capabilities"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="IssueReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(choices=[("bug", "Xatolik"), ("validation", "Forma / ma'lumot xatosi"), ("performance", "Sekin ishlash"), ("other", "Boshqa")], default="other", max_length=20)),
                ("module", models.CharField(blank=True, max_length=40)),
                ("message", models.TextField(blank=True)),
                ("page_url", models.CharField(blank=True, max_length=500)),
                ("user_agent", models.CharField(blank=True, max_length=300)),
                ("console_errors", models.JSONField(blank=True, default=list)),
                ("failed_requests", models.JSONField(blank=True, default=list)),
                ("screenshot", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("new", "Yangi"), ("resolved", "Hal qilindi")], default="new", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("organization", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="issue_reports", to="organization.organization")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="issue_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
