from django.contrib import admin

from .models import SignupAttribution, Visit


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("created_at", "source", "medium", "campaign", "referrer_host", "landing_path")
    list_filter = ("source", "medium")
    search_fields = ("campaign", "referrer_host", "visitor_id")
    date_hierarchy = "created_at"


@admin.register(SignupAttribution)
class SignupAttributionAdmin(admin.ModelAdmin):
    list_display = ("organization", "source", "medium", "campaign", "last_source", "first_seen_at", "created_at")
    list_filter = ("source", "medium")
    search_fields = ("organization__nomi", "campaign")
    raw_id_fields = ("organization",)
