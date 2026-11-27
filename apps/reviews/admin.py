from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("book", "reader", "rating", "is_hidden", "updated_at")
    list_filter = ("is_hidden", "rating")
    search_fields = ("book__nomi", "reader__fish", "text")
