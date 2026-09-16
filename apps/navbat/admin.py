from django.contrib import admin

from .models import Navbat


@admin.register(Navbat)
class NavbatAdmin(admin.ModelAdmin):
    list_display = ("id", "kitob", "oquvchi", "holati", "navbat_sanasi", "taklif_muddati")
    list_filter = ("holati",)
    search_fields = ("kitob__nomi", "oquvchi__fish")
