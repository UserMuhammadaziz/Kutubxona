from rest_framework import serializers

from .models import KitobXabari, TelegramBot


class TelegramBotSerializer(serializers.ModelSerializer):
    webhook_url = serializers.SerializerMethodField()

    class Meta:
        model = TelegramBot
        fields = [
            "id",
            "organization",
            "telegram_bot_id",
            "username",
            "holati",
            "webhook_ornatilgan",
            "webhook_url",
            "oxirgi_tekshiruv",
            "oxirgi_xato",
            "yaratilgan",
        ]
        read_only_fields = fields

    def get_webhook_url(self, obj):
        from django.conf import settings

        return (
            f"{settings.TELEGRAM_WEBHOOK_BASE_URL.rstrip('/')}"
            f"/api/telegram/webhook/{obj.webhook_path}/"
        )


class KitobXabariSerializer(serializers.ModelSerializer):
    kitob_nomi = serializers.CharField(source="kitob.nomi", read_only=True)

    class Meta:
        model = KitobXabari
        fields = [
            "id",
            "kitob",
            "kitob_nomi",
            "tur",
            "yuborildi",
            "yuborilgan_soni",
            "xato",
            "yaratilgan",
            "yuborilgan_sana",
        ]
        read_only_fields = fields
