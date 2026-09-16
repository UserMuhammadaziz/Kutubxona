from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "username", "full_name", "rol", "telefon", "is_active", "is_staff")
    list_filter = ("rol", "is_active")
    search_fields = ("username", "full_name", "telefon")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Kutubxona ma'lumotlari", {"fields": ("full_name", "rol", "telefon")}),
    )
