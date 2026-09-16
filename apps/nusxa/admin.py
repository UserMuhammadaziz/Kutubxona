from django.contrib import admin

from .models import Nusxa


@admin.register(Nusxa)
class NusxaAdmin(admin.ModelAdmin):
    list_display = ("id", "inventar_raqami", "kitob", "holati", "javon", "qabul_sana")
    list_filter = ("holati", "javon")
    search_fields = ("inventar_raqami", "kitob__nomi")
    autocomplete_fields = ("kitob",)
