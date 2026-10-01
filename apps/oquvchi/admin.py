from django.contrib import admin, messages
from django.db import transaction

from .models import Ariza, Oquvchi
from . import services


@admin.register(Oquvchi)
class OquvchiAdmin(admin.ModelAdmin):
    list_display = ("id", "fish", "sinf", "telefon", "karta_raqami", "telegram_id", "faol", "royxat_sanasi")
    list_filter = ("faol", "sinf")
    search_fields = ("fish", "telefon", "karta_raqami")


@admin.register(Ariza)
class ArizaAdmin(admin.ModelAdmin):
    """A'zolik arizalari — kutubxonachi ham REST API orqali, ham Django admin
    orqali qabul/rad eta oladi. Ikkalasi ham bitta servis funksiyasini
    chaqiradi, shuning uchun Telegram xabari ham bir xil yuboriladi."""

    list_display = ("id", "fish", "sinf", "telefon", "telegram_id", "holati", "ariza_sanasi")
    list_filter = ("holati", "sinf")
    search_fields = ("fish", "telefon", "telegram_id")
    # `holati` va `tasdiqlangan_sana` ni qo'lda tahrirlashga yo'l qo'yilmaydi:
    # aks holda o'quvchiga Telegram xabari yuborilmay qolardi. Holat faqat
    # quyidagi ikkita action orqali o'zgaradi.
    readonly_fields = ("ariza_sanasi", "tasdiqlangan_sana", "telegram_id", "holati")
    actions = ("arizani_tasdiqlash", "arizani_rad_etish")

    @admin.action(description="Tanlangan arizalarni TASDIQLASH (o'quvchi yaratiladi)")
    def arizani_tasdiqlash(self, request, queryset):
        tasdiqlangan = 0
        for ariza in queryset.filter(holati="kutmoqda"):
            if Oquvchi.objects.filter(telegram_id=ariza.telegram_id).exists():
                self.message_user(
                    request,
                    f"{ariza.fish}: bu Telegram akkaunt allaqachon o'quvchiga bog'langan.",
                    level=messages.WARNING,
                )
                continue
            try:
                with transaction.atomic():
                    ariza, oquvchi, yangi_karta = services.arizani_tasdiqla(ariza)
                    services.ariza_holatini_yubor(
                        ariza, services.tasdiqlash_xabari(ariza, oquvchi, yangi_karta)
                    )
            except ValueError as e:
                self.message_user(request, str(e), level=messages.WARNING)
                continue
            tasdiqlangan += 1
        yopilgan = queryset.exclude(holati="kutmoqda").count()
        self.message_user(
            request,
            f"{tasdiqlangan} ta ariza tasdiqlandi"
            + (f", {yopilgan} ta allaqachon yopilgan bo'lib qoldi" if yopilgan else ""),
            level=messages.SUCCESS,
        )

    @admin.action(description="Tanlangan arizalarni RAD ETISH")
    def arizani_rad_etish(self, request, queryset):
        rad = 0
        for ariza in queryset.filter(holati="kutmoqda"):
            with transaction.atomic():
                services.arizani_rad_et(ariza, "Kutubxonada rad etildi")
                services.ariza_holatini_yubor(
                    ariza, services.rad_etilgan_xabari(ariza, ariza.izoh)
                )
            rad += 1
        self.message_user(request, f"{rad} ta ariza rad etildi", level=messages.SUCCESS)
