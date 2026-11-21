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


class XabarYuborishSerializer(serializers.Serializer):
    """Kutubxonachining o'quvchi/o'qituvchilarga xabar yuborish so'rovi."""

    TURLAR = (("shaxs", "Bitta kitobxon"), ("sinf", "Sinf"), ("hamma", "Barcha sinflar"))
    ROLLAR = (("oquvchi", "O'quvchi"), ("oqituvchi", "O'qituvchi"))

    tur = serializers.ChoiceField(choices=TURLAR)
    rol = serializers.ChoiceField(choices=ROLLAR)
    oquvchi = serializers.IntegerField(required=False, min_value=1)
    sinf = serializers.CharField(required=False, allow_blank=True, max_length=30)
    matn = serializers.CharField(max_length=3000, trim_whitespace=True)

    def validate(self, attrs):
        if attrs["tur"] == "shaxs" and not attrs.get("oquvchi"):
            raise serializers.ValidationError({"oquvchi": "Kitobxonni tanlang."})
        if attrs["tur"] == "sinf" and not (attrs.get("sinf") or "").strip():
            raise serializers.ValidationError({"sinf": "Sinfni tanlang."})
        if attrs["tur"] == "sinf":
            attrs["sinf"] = attrs["sinf"].strip()
        return attrs


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
