# apps/oquvchi/serializers.py
from datetime import date

from rest_framework import serializers

from .constants import FANLAR, FISH_RE, SINF_RE
from .models import Ariza, Oquvchi
from .services import oquvchi_yarat

# Ariza.rol va Oquvchi.rol uchun bir xil qiymatlar (models.RUL_CHOICES ga
# qarab qo'lda yoziladi, chunki serializer import paytida model sinflariga
# murojaat qilmasligimiz kerak).
ROL_CHOICES = [("oquvchi", "Oquvchi"), ("oqituvchi", "O'qituvchi")]


class OquvchiSerializer(serializers.ModelSerializer):
    """O'quvchilar ro'yxati / kartochkasi uchun asosiy serializer."""

    class Meta:
        model = Oquvchi
        fields = [
            "id",
            "rol",
            "fish",
            "telefon",
            "telegram_id",
            "karta_raqami",
            "sinf",
            "kasb",
            "tugilgan_sana",
            "manzil",
            "royxat_sanasi",
            "faol",
            "qayta_ariza_kerak",
        ]
        read_only_fields = [
            "id",
            "karta_raqami",
            "telegram_id",
            "royxat_sanasi",
            "qayta_ariza_kerak",
        ]


class OquvchiYaratishSerializer(serializers.ModelSerializer):
    """POST /api/readers/ — karta_raqami avtomatik generatsiya qilinadi.

    `rol="oqituvchi"` yuborilsa fan (`kasb`) majburiy bo'ladi."""

    rol = serializers.ChoiceField(choices=ROL_CHOICES, required=False, default="oquvchi")

    class Meta:
        model = Oquvchi
        # Faqat ism-familiya, telefon va rolga qarab sinf/fan so'raladi.
        fields = ["id", "rol", "fish", "telefon", "sinf", "kasb", "karta_raqami"]
        read_only_fields = ["id", "karta_raqami"]

    def validate(self, attrs):
        if attrs.get("rol") == "oqituvchi":
            kasb = (attrs.get("kasb") or "").strip()
            if not kasb:
                raise serializers.ValidationError(
                    {"kasb": "O'qituvchi uchun fani ko'rsating (masalan: Matematika)."}
                )
            attrs["kasb"] = kasb
            attrs["sinf"] = ""
        return attrs

    def validate_telefon(self, value):
        if Oquvchi.objects.filter(telefon=value).exists():
            raise serializers.ValidationError(
                "Bu telefon raqamiga allaqachon o'quvchi kartasi ochilgan."
            )
        return value

    def create(self, validated_data):
        return oquvchi_yarat(**validated_data)


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


class ArizaSerializer(serializers.ModelSerializer):
    """Arizalar ro'yxati / tasdiqlash uchun (kutubxonachi)."""

    class Meta:
        model = Ariza
        fields = [
            "id",
            "telegram_id",
            "fish",
            "telefon",
            "rol",
            "sinf",
            "kasb",
            "tugilgan_sana",
            "manzil",
            "holati",
            "ariza_sanasi",
            "tasdiqlangan_sana",
            "izoh",
            "qayta_ariza_kerak",
        ]
        read_only_fields = [
            "id",
            "ariza_sanasi",
            "tasdiqlangan_sana",
            "holati",
            "izoh",
            "rol",
            "qayta_ariza_kerak",
        ]


class ArizaYaratishSerializer(serializers.ModelSerializer):
    """POST /api/applications/ — bot orqali yangi a'zolik arizasi.

    Bot rolni oldindan tanlaydi va shunga qarab so'raydi:
    • `rol="oquvchi"`    → ism-familiya, telefon va sinf;
    • `rol="oqituvchi"` → ism-familiya, telefon va kasb (o'qitayotgan fan).

    tugilgan_sana va manzil ixtiyoriy (eski arizalar bilan moslik uchun) —
    yangi bot ularni so'ramaydi."""

    telegram_id = serializers.IntegerField(validators=[])
    # Ikkala maydon ham ixtiyoriy bo'lib yoziladi: qaysi biri to'ldirilishi
    # `validate()` ichida rolga qarab aniqlanadi. Aks holda o'qituvchi arizasida
    # bo'sh `sinf`, o'quvchi arizasida bo'sh `kasb` "maydan bo'sh" xatosini
    # keltirib chiqarardi.
    sinf = serializers.CharField(
        max_length=30, required=False, allow_blank=True, allow_null=True
    )
    kasb = serializers.CharField(
        max_length=60, required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        model = Ariza
        fields = [
            "telegram_id",
            "fish",
            "telefon",
            "rol",
            "sinf",
            "kasb",
            "tugilgan_sana",
            "manzil",
        ]

    def validate_tugilgan_sana(self, value):
        if value and value > date.today():
            raise serializers.ValidationError(
                "Tug'ilgan sana kelajakda bo'lishi mumkin emas."
            )
        return value

    def validate_fish(self, value):
        """Ism-familiya — kamida ikki so'z, faqat harflar."""
        fish = (value or "").strip()
        if not FISH_RE.fullmatch(fish):
            raise serializers.ValidationError(
                "Ism-familiya «Ism Familiya» formatida yozilishi kerak "
                "(kamida ikki so'z, raqamsiz)."
            )
        return fish

    def validate_sinf(self, value):
        """Sinf — 7-A / 9-B / 10- ko'rinishida bo'lishi shart."""
        if value is None:
            return value
        sinf = value.strip()
        if not sinf:
            return sinf
        if not SINF_RE.fullmatch(sinf):
            raise serializers.ValidationError(
                "Sinf «7-A», «9-B» yoki «10-» formatida yozilishi kerak."
            )
        return sinf

    def validate_kasb(self, value):
        """O'qituvchi fanni bot taklif qilgan ro'yxatdan tanlaydi."""
        if not value:
            return value
        fanlar = [fan.strip() for fan in value.split(",") if fan.strip()]
        notogri = [fan for fan in fanlar if fan not in FANLAR]
        if notogri:
            raise serializers.ValidationError(
                "Fanlardan faqat bot ko'rsatgan ro'yxatdan tanlash mumkin: "
                + ", ".join(notogri)
            )
        return ", ".join(fanlar)

    def validate(self, attrs):
        rol = attrs.get("rol") or "oquvchi"
        attrs["rol"] = rol

        if rol == "oqituvchi":
            # O'qituvchi uchun sinf kerak emas, faqat kasb majburiy.
            attrs["sinf"] = None
            kasb = (attrs.get("kasb") or "").strip()
            if not kasb:
                raise serializers.ValidationError(
                    {"kasb": "Kasbingizni ko'rsating (masalan: Matematika)."}
                )
            if len(kasb) > 60:
                raise serializers.ValidationError(
                    {"kasb": "Kasb nomi juda uzun (maksimum 60 belgi)."}
                )
            attrs["kasb"] = kasb
        else:
            # Oquvchi uchun sinf majburiy, kasb kerak emas.
            sinf = (attrs.get("sinf") or "").strip()
            if not sinf:
                raise serializers.ValidationError({"sinf": "Sinfni ko'rsating (masalan: 7-A)."})
            if len(sinf) > 30:
                raise serializers.ValidationError(
                    {"sinf": "Sinf nomi juda uzun (maksimum 30 belgi)."}
                )
            attrs["sinf"] = sinf
            attrs["kasb"] = ""

        telegram_id = attrs["telegram_id"]
        # Eski formatda ariza yuborgan (qabul qilingan ham) foydalanuvchilarga
        # yangi formatda qaytadan ariza topshirishga ruxsat beramiz.
        bandlangan = Oquvchi.objects.filter(telegram_id=telegram_id).exclude(
            qayta_ariza_kerak=True
        ).exists()
        if bandlangan:
            raise serializers.ValidationError(
                {"error": "allaqachon_azo", "detail": "Bu telegram akkaunt allaqachon ro'yxatdan o'tgan"}
            )

        kutmoqdagi = Ariza.objects.filter(telegram_id=telegram_id, holati="kutmoqda").first()
        if kutmoqdagi and not kutmoqdagi.qayta_ariza_kerak:
            raise serializers.ValidationError(
                {"error": "ariza_kutmoqda", "detail": "Arizangiz hali ko'rib chiqilmoqda"}
            )
        # Eski (noto'g'ri formatdagi, bekor yoki tasdiqlangan) arizalar yangi
        # ariza ochish uchun o'chiriladi.
        Ariza.objects.filter(telegram_id=telegram_id).delete()
        return attrs


class ArizaStatusSerializer(serializers.Serializer):
    """GET /api/applications/status/?telegram_id= — bot uchun ariza holati."""

    holati = serializers.CharField()
    izoh = serializers.CharField(required=False, allow_blank=True)
    qayta_ariza_kerak = serializers.BooleanField(default=False)