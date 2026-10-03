from rest_framework import serializers
from kitob.models import Kitob
from nusxa.models import Nusxa


class NusxaSerializer(serializers.ModelSerializer):
    """Nusxalar ro'yxati / yaratish / holat o'zgartirish uchun."""

    kitob_nomi = serializers.CharField(source="kitob.nomi", read_only=True)

    class Meta:
        model = Nusxa
        fields = [
            "id",
            "kitob",
            "kitob_nomi",
            "inventar_raqami",
            "holati",
            "javon",
            "qabul_sana",
            "izoh",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        # Kutubxonachi faqat tamirda / yoqolgan / mavjud ga o'zgartira
        # oladi — `berilgan` va `band` holatlari `/api/loans/` hamda
        # navbat jarayonlari orqali qo'yiladi. Qo'lda qo'yilsa, Berish/
        # Navbat yozuvlari bilan mos kelmaydi va keyingi berishda
        # `IntegrityError` (500) chiqadi.
        holati = attrs.get("holati")
        if holati in ("berilgan", "band"):
            raise serializers.ValidationError(
                {
                    "holati": (
                        "Bu holatga faqat kitob berish/navbat jarayonlari "
                        "orqali o'tiladi, qo'lda qo'yib bo'lmaydi."
                    )
                }
            )
        return attrs

    def validate_kitob(self, value):
        if not Kitob.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Ko'rsatilgan kitob topilmadi.")
        return value


class NusxaYaratishSerializer(serializers.ModelSerializer):
    """POST /api/copies/ — inventar raqami bilan yangi nusxa qo'shish."""

    class Meta:
        model = Nusxa
        fields = ["id", "kitob", "inventar_raqami", "javon", "qabul_sana", "izoh"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data.setdefault("holati", "mavjud")
        return super().create(validated_data)