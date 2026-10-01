# apps/navbat/serializers.py
from rest_framework import serializers

from kitob.models import Kitob
from oquvchi.models import Oquvchi
from .models import Navbat


class NavbatSerializer(serializers.ModelSerializer):
    """Navbat yozuvini to'liq ko'rsatish uchun (kutubxonachi/hisobot)."""

    kitob_nomi = serializers.CharField(source="kitob.nomi", read_only=True)
    oquvchi_fish = serializers.CharField(source="oquvchi.fish", read_only=True)

    class Meta:
        model = Navbat
        fields = [
            "id",
            "kitob",
            "kitob_nomi",
            "oquvchi",
            "oquvchi_fish",
            "navbat_sanasi",
            "holati",
            "ajratilgan_nusxa",
            "taklif_vaqti",
            "taklif_muddati",
            "javob_vaqti",
            "javob",
            "bekor_sababi",
        ]
        read_only_fields = [
            "id",
            "navbat_sanasi",
            "holati",
            "ajratilgan_nusxa",
            "taklif_vaqti",
            "taklif_muddati",
            "javob_vaqti",
            "javob",
            "bekor_sababi",
        ]


class NavbatYaratishSerializer(serializers.Serializer):
    """POST /api/reservations/ — kitob navbatiga turish.
    Javobida nechanchi o'rin ekani orin maydonida qaytariladi.
    O'quvchi bot orqali qo'shilsa telegram_id, kutubxonachi veb-orginal
    orqali qo'shilsa oquvchi (PK) kiritiladi — ikkalasi ham qo'llab-quvvatlanadi.
    """

    kitob = serializers.PrimaryKeyRelatedField(queryset=Kitob.objects.all())
    oquvchi = serializers.PrimaryKeyRelatedField(queryset=Oquvchi.objects.all(), required=False)
    telegram_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        if "oquvchi" not in attrs and "telegram_id" not in attrs:
            raise serializers.ValidationError(
                {"error": "oquvchi_kerak", "detail": "oquvchi yoki telegram_id kiritilishi shart"}
            )
        oquvchi = attrs.get("oquvchi")
        if oquvchi is None and "telegram_id" in attrs:
            try:
                oquvchi = Oquvchi.objects.get(telegram_id=attrs["telegram_id"])
            except Oquvchi.DoesNotExist:
                raise serializers.ValidationError(
                    {"error": "oquvchi_topilmadi", "detail": "O'quvchi bog'lanmagan"}
                )
            attrs["oquvchi"] = oquvchi
        if not oquvchi.faol:
            raise serializers.ValidationError(
                {"error": "oquvchi_bloklangan", "detail": "O'quvchi bloklangan"}
            )
        if Navbat.objects.filter(
            kitob=attrs["kitob"],
            oquvchi=oquvchi,
            holati__in=["kutmoqda", "taklif_qilindi"],
        ).exists():
            raise serializers.ValidationError(
                {"error": "allaqachon_navbatda", "detail": "Siz bu kitobga allaqachon navbatdasiz"}
            )
        return attrs


class NavbatJavobSerializer(serializers.Serializer):
    """POST /api/reservations/{id}/respond/ — {"javob": "olaman" | "kerak_emas"}"""

    JAVOB_CHOICES = ("olaman", "kerak_emas")

    javob = serializers.ChoiceField(choices=JAVOB_CHOICES)

    def validate(self, attrs):
        navbat: Navbat = self.instance
        if navbat.holati != "taklif_qilindi":
            raise serializers.ValidationError(
                {"error": "taklif_yoq", "detail": "Sizga hozircha taklif yuborilmagan"}
            )
        return attrs


class NavbatMeniSerializer(serializers.ModelSerializer):
    """GET /api/reservations/my/?telegram_id= — o'quvchining navbatlari va o'rni."""

    kitob_nomi = serializers.CharField(source="kitob.nomi", read_only=True)
    orin = serializers.SerializerMethodField()

    class Meta:
        model = Navbat
        fields = ["id", "kitob_nomi", "holati", "javob", "navbat_sanasi", "taklif_muddati", "orin"]

    def get_orin(self, obj):
        if obj.holati != "kutmoqda":
            return None
        return (
            Navbat.objects.filter(
                kitob=obj.kitob,
                holati="kutmoqda",
                navbat_sanasi__lte=obj.navbat_sanasi,
            ).count()
        )