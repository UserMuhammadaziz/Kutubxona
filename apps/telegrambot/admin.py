from django.contrib import admin

from .models import KitobXabari, TelegramBot, TelegramSession, TelegramUpdate


@admin.register(TelegramBot)
class TelegramBotAdmin(admin.ModelAdmin):
    list_display = ["username", "organization", "holati", "webhook_ornatilgan", "oxirgi_tekshiruv"]
    list_filter = ["holati", "webhook_ornatilgan"]
    search_fields = ["username", "organization__nomi"]
    exclude = ["token_encrypted"]


@admin.register(TelegramSession)
class TelegramSessionAdmin(admin.ModelAdmin):
    list_display = ["telegram_id", "bot", "step", "yangilangan"]
    list_filter = ["step"]


@admin.register(TelegramUpdate)
class TelegramUpdateAdmin(admin.ModelAdmin):
    list_display = ["bot", "update_id", "qabul_qilindi"]


@admin.register(KitobXabari)
class KitobXabariAdmin(admin.ModelAdmin):
    list_display = ["kitob", "tur", "yuborildi", "yuborilgan_soni", "yaratilgan"]
    list_filter = ["tur", "yuborildi"]
