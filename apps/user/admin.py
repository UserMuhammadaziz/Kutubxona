from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from organization.models import Membership

from .models import ChatXabar, User, XatolikXabari


class UserMembershipInline(admin.TabularInline):
    """Library and role (Egasi / Administrator / Kutubxonachi) of the account."""

    model = Membership
    fk_name = "user"
    extra = 1
    fields = ("organization", "rol", "faol")
    verbose_name = "Kutubxonadagi roli"
    verbose_name_plural = "Kutubxonalar va rollar"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "username", "full_name", "rol", "telefon", "is_active", "is_staff")
    list_filter = ("rol", "is_active")
    search_fields = ("username", "full_name", "telefon")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Kutubxona ma'lumotlari", {"fields": ("full_name", "rol", "telefon")}),
    )
    # The stock add form only asks for username and password.
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("username", "password1", "password2")}),
        ("Kutubxona ma'lumotlari", {"fields": ("full_name", "telefon", "rol")}),
        ("Platforma", {"fields": ("is_staff",), "description": "Belgilansa, /platform bo'limiga kira oladi."}),
    )
    inlines = [UserMembershipInline]


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


@admin.register(XatolikXabari)
class XatolikXabariAdmin(admin.ModelAdmin):
    list_display = ("id", "yaratilgan", "tur", "yuborgan", "organization", "sahifa")
    list_filter = ("tur", "organization")
    search_fields = ("matn", "sahifa")
    readonly_fields = ("yaratilgan",)

