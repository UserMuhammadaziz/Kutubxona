# apps/oquvchi/serializers.py
from datetime import date

from rest_framework import serializers

from .models import Oquvchi


def _yangi_karta_raqami():
    """LIB-{yil}-{4 xonali tartib raqam} formatida keyingi bo'sh raqamni topadi."""
    yil = date.today().year
    prefiks = f"LIB-{yil}-"
    oxirgi = (
        Oquvchi.objects.filter(karta_raqami__startswith=prefiks)
        .order_by("-karta_raqami")
        .first()
    )
    if oxirgi:
        try:
            tartib = int(oxirgi.karta_raqami.split("-")[-1]) + 1
        except ValueError:
            tartib = 1
    else:
        tartib = 1
    return f"{prefiks}{tartib:04d}"


class OquvchiSerializer(serializers.ModelSerializer):
    """O'quvchilar ro'yxati / kartochkasi uchun asosiy serializer."""

    class Meta:
        model = Oquvchi
        fields = [
            "id",
            "fish",
            "telefon",
            "telegram_id",
            "karta_raqami",
            "tugilgan_sana",
            "manzil",
            "royxat_sanasi",
            "faol",
        ]
        read_only_fields = ["id", "karta_raqami", "telegram_id", "royxat_sanasi"]


class OquvchiYaratishSerializer(serializers.ModelSerializer):
    """POST /api/readers/ — karta_raqami avtomatik generatsiya qilinadi."""

    class Meta:
        model = Oquvchi
        fields = ["id", "fish", "telefon", "tugilgan_sana", "manzil", "karta_raqami"]
        read_only_fields = ["id", "karta_raqami"]

    def validate_telefon(self, value):
        if Oquvchi.objects.filter(telefon=value).exists():
            raise serializers.ValidationError(
                "Bu telefon raqamiga allaqachon o'quvchi kartasi ochilgan."
            )
        return value

    def create(self, validated_data):
        validated_data["karta_raqami"] = _yangi_karta_raqami()
        return super().create(validated_data)


class OquvchiBindSerializer(serializers.Serializer):
    """POST /api/readers/bind/ — bot telefon + karta_raqami bo'yicha
    telegram_id ni bog'laydi."""

    telefon = serializers.CharField()
    karta_raqami = serializers.CharField()
    telegram_id = serializers.IntegerField()

    def validate(self, attrs):
        try:
            oquvchi = Oquvchi.objects.get(
                telefon=attrs["telefon"], karta_raqami=attrs["karta_raqami"]
            )
        except Oquvchi.DoesNotExist:
            raise serializers.ValidationError(
                {"error": "topilmadi", "detail": "Ma'lumot topilmadi, kutubxonachiga murojaat qiling"}
            )
        if (
            Oquvchi.objects.filter(telegram_id=attrs["telegram_id"])
            .exclude(pk=oquvchi.pk)
            .exists()
        ):
            raise serializers.ValidationError(
                {"error": "band", "detail": "Bu telegram akkaunt boshqa o'quvchiga bog'langan"}
            )
        attrs["oquvchi"] = oquvchi
        return attrs

    def save(self, **kwargs):
        oquvchi = self.validated_data["oquvchi"]
        oquvchi.telegram_id = self.validated_data["telegram_id"]
        oquvchi.save(update_fields=["telegram_id"])
        return oquvchi