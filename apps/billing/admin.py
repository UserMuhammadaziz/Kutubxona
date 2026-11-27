from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "plan", "months", "amount", "method", "status", "created_at", "paid_at")
    list_filter = ("status", "method")
    search_fields = ("organization__nomi", "provider_payment_id")
    readonly_fields = [f.name for f in Payment._meta.fields]
