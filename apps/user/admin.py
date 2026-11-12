from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import ChatXabar, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "username", "full_name", "rol", "telefon", "is_active", "is_staff")
    list_filter = ("rol", "is_active")
    search_fields = ("username", "full_name", "telefon")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Kutubxona ma'lumotlari", {"fields": ("full_name", "rol", "telefon")}),
    )


@admin.register(ChatXabar)
class ChatXabarAdmin(admin.ModelAdmin):
    """AI suhbatlari — faqat platforma xodimlari uchun, statistika maqsadida."""

    list_display = ("id", "user", "rol", "qisqa_matn", "yaratilgan")
    list_filter = ("rol",)
    search_fields = ("matn", "user__username")
    date_hierarchy = "yaratilgan"

    @admin.display(description="Matn")
    def qisqa_matn(self, obj):
        return obj.matn[:80]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
