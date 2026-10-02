from django.contrib import admin

from .models import Berish


@admin.register(Berish)
class BerishAdmin(admin.ModelAdmin):
    list_display = (
        "id", "nusxa", "oquvchi", "berilgan_sana",
        "qaytarish_muddati", "qaytarilgan_sana", "holati",
    )
    list_filter = ("holati",)
    search_fields = ("nusxa__inventar_raqami", "kitob__nomi", "oquvchi__fish", "oquvchi__telefon")
    autocomplete_fields = ("nusxa", "oquvchi", "bergan_xodim", "olgan_xodim")
