from django.contrib import admin

from .models import Membership, Organization


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    autocomplete_fields = []


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["nomi", "slug", "faol", "egasi", "yaratilgan"]
    list_filter = ["faol"]
    search_fields = ["nomi", "slug", "telefon"]
    prepopulated_fields = {"slug": ("nomi",)}
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "organization", "rol", "faol", "telegram_id"]
    list_filter = ["rol", "faol", "organization"]
    search_fields = ["user__username", "user__full_name", "organization__nomi"]
