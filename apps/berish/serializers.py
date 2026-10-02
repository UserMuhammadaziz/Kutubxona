from datetime import date
from rest_framework import serializers
from kitob.models import Kitob
from nusxa.models import Nusxa
from oquvchi.models import Oquvchi
from .models import Berish


class BerishSerializer(serializers.ModelSerializer):
    """GET /api/loans/ — berishlar ro'yxati (kutubxonachi uchun)."""

    kitob_nomi = serializers.CharField(source="kitob.nomi", read_only=True)
    inventar_raqami = serializers.SerializerMethodField()
    oquvchi_fish = serializers.CharField(source="oquvchi.fish", read_only=True)

    class Meta:
        model = Berish
        fields = [
            "id",
            "nusxa",
            "kitob",
            "kitob_nomi",
            "inventar_raqami",
            "asli",
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
            "kitob",
            "berilgan_sana",
            "qaytarish_muddati",
            "qaytarilgan_sana",
            "olgan_xodim",
            "holati",
            "eslatma_yuborilgan",
        ]

    def get_inventar_raqami(self, obj):
        # Nusxasi yo'q kitob «asli» holda berilgan — inventar raqami yo'q.
        return obj.nusxa.inventar_raqami if obj.nusxa_id else ""

    @staticmethod
    def _asli(obj):
        return obj.nusxa_id is None

    asli = serializers.SerializerMethodField()


class BerishYaratishSerializer(serializers.Serializer):
    """POST /api/loans/ — kitob berish. Barcha biznes cheklovlar
    (limit_oshdi, tolanmagan_jarima, nusxa_band, barcha_nusxalar_berilgan,
    oquvchi_bloklangan) services qatlamida tekshiriladi; bu serializer
    faqat kirish ma'lumotini valid qiladi.

    Ikki xil berish bor:
    * `nusxa` — aniq nusxa beriladi;
    * `kitob` — kitob bo'yicha berish: mavjud nusxa topiladi, yo'q bo'lsa
      aslini beriladi, hammasi band bo'lsa avtomatik navbatga qo'shiladi.
    """

    nusxa = serializers.PrimaryKeyRelatedField(
        queryset=Nusxa.objects.all(), required=False
    )
    kitob = serializers.PrimaryKeyRelatedField(
        queryset=Kitob.objects.all(), required=False
    )
    oquvchi = serializers.PrimaryKeyRelatedField(queryset=Oquvchi.objects.all())

    def validate(self, attrs):
        if bool(attrs.get("nusxa")) == bool(attrs.get("kitob")):
            raise serializers.ValidationError(
                {
                    "error": "notogri_manzil",
                    "detail": "Nusxa yoki kitobdan birini tanlang",
                }
            )
        return attrs

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

    kitob_nomi = serializers.CharField(source="kitob.nomi", read_only=True)
    inventar_raqami = serializers.SerializerMethodField()
    asli = serializers.SerializerMethodField()
    qolgan_kun = serializers.SerializerMethodField()

    class Meta:
        model = Berish
        fields = [
            "id",
            "kitob_nomi",
            "inventar_raqami",
            "asli",
            "berilgan_sana",
            "qaytarish_muddati",
            "qolgan_kun",
        ]

    def get_inventar_raqami(self, obj):
        return obj.nusxa.inventar_raqami if obj.nusxa_id else ""

    def get_asli(self, obj):
        return obj.nusxa_id is None

    def get_qolgan_kun(self, obj):
        return (obj.qaytarish_muddati - date.today()).days