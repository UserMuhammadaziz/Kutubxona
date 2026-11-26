from django.utils import timezone
from rest_framework import serializers
from nusxa.models import Nusxa
from organization.tenancy import TenantSerializerMixin


class NusxaSerializer(TenantSerializerMixin, serializers.ModelSerializer):
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


class NusxaYaratishSerializer(TenantSerializerMixin, serializers.ModelSerializer):
    """POST /api/copies/ — inventar raqami bilan yangi nusxa qo'shish."""

    class Meta:
        model = Nusxa
        fields = ["id", "kitob", "inventar_raqami", "javon", "qabul_sana", "izoh"]
        read_only_fields = ["id"]
        # Received date defaults to today when the client omits it.
        extra_kwargs = {"qabul_sana": {"required": False}}

    def validate_inventar_raqami(self, value):
        # Unique per organization; `organization` is not a serializer field,
        # so DRF would not catch this and the DB constraint would raise a 500.
        org = self._organization()
        if org is not None and Nusxa.objects.filter(organization=org, inventar_raqami=value).exists():
            raise serializers.ValidationError("Bu inventar raqami allaqachon mavjud.")
        return value

    def create(self, validated_data):
        validated_data.setdefault("holati", "mavjud")
        validated_data.setdefault("qabul_sana", timezone.localdate())
        return super().create(validated_data)