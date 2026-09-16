from django.contrib import admin

from .models import Oquvchi


@admin.register(Oquvchi)
class OquvchiAdmin(admin.ModelAdmin):
    list_display = ("id", "fish", "telefon", "karta_raqami", "telegram_id", "faol", "royxat_sanasi")
    list_filter = ("faol",)
    search_fields = ("fish", "telefon", "karta_raqami")
