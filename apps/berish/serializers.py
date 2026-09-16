from datetime import date
from rest_framework import serializers
from nusxa.models import Nusxa
from oquvchi.models import Oquvchi
from .models import Berish


class BerishSerializer(serializers.ModelSerializer):
    """GET /api/loans/ — berishlar ro'yxati (kutubxonachi uchun)."""

    kitob_nomi = serializers.CharField(source="nusxa.kitob.nomi", read_only=True)
    inventar_raqami = serializers.CharField(source="nusxa.inventar_raqami", read_only=True)
    oquvchi_fish = serializers.CharField(source="oquvchi.fish", read_only=True)

    class Meta:
        model = Berish
        fields = [
            "id",
            "nusxa",
            "kitob_nomi",
            "inventar_raqami",
            "oquvchi",
            "oquvchi_fish",
            "bergan_xodim",
            "olgan_xodim",
            "berilgan_sana",
            "qaytarish_muddati",
            "qaytarilgan_sana",
            "holati",
            "eslatma_yuborilgan",
        ]
        read_only_fields = [
            "id",
            "berilgan_sana",
            "qaytarish_muddati",
            "qaytarigan_sana",
            "olgan_xodim",
            "holati",
            "eslatma_yuborilgan",
        ]


class BerishYaratishSerializer(serializers.Serializer):
    """POST /api/loans/ — kitob berish. Barcha biznes cheklovlar
    (limit_oshdi, tolanmagan_jarima, nusxa_band, oquvchi_bloklangan,
    navbat_boshqada) view/services qatlamida tekshiriladi; bu serializer
    faqat kirish ma'lumotini valid qiladi."""

    nusxa = serializers.PrimaryKeyRelatedField(queryset=Nusxa.objects.all())
    oquvchi = serializers.PrimaryKeyRelatedField(queryset=Oquvchi.objects.all())

    def validate_nusxa(self, value):
        if value.holati != "mavjud":
            raise serializers.ValidationError(
                {"error": "nusxa_band", "detail": "Bu nusxa hozir mavjud emas"}
            )
        return value

    def validate_oquvchi(self, value):
        if not value.faol:
            raise serializers.ValidationError(
                {"error": "oquvchi_bloklangan", "detail": "O'quvchi bloklangan"}
            )
        return value


class BerishQaytarishSerializer(serializers.Serializer):
    """POST /api/loans/{id}/return/ — bo'sh body, hisob-kitob services.py
    da bajariladi, natija shu shaklda qaytariladi."""

    jarima_summasi = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    kechikkan_kunlar = serializers.IntegerField(required=False)
    navbatga_taklif_ketdimi = serializers.BooleanField(required=False, default=False)


class BerishMeniSerializer(serializers.ModelSerializer):
    """GET /api/loans/my/?telegram_id= — o'quvchining joriy kitoblari."""

    kitob_nomi = serializers.CharField(source="nusxa.kitob.nomi", read_only=True)
    inventar_raqami = serializers.CharField(source="nusxa.inventar_raqami", read_only=True)
    qolgan_kun = serializers.SerializerMethodField()

    class Meta:
        model = Berish
        fields = [
            "id",
            "kitob_nomi",
            "inventar_raqami",
            "berilgan_sana",
            "qaytarish_muddati",
            "qolgan_kun",
        ]

    def get_qolgan_kun(self, obj):
        return (obj.qaytarish_muddati - date.today()).days