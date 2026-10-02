from django.contrib import admin

from .models import Jarima


@admin.register(Jarima)
class JarimaAdmin(admin.ModelAdmin):
    list_display = ("id", "berish", "kechikkan_kunlar", "summa", "tolandimi", "tolangan_sana")
    list_filter = ("tolandimi",)
    search_fields = ("berish__oquvchi__fish", "berish__nusxa__inventar_raqami", "berish__kitob__nomi")
