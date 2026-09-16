from django.contrib import admin

from .models import Kitob


@admin.register(Kitob)
class KitobAdmin(admin.ModelAdmin):
    list_display = ("id", "nomi", "muallif", "janr", "nashr_yili", "isbn", "qoshilgan_sana")
    list_filter = ("janr", "nashr_yili")
    search_fields = ("nomi", "muallif", "isbn")
    ordering = ("nomi",)
