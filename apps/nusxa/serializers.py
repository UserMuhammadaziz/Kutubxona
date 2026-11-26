import re

from django.db import transaction
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


MAX_COPIES_PER_REQUEST = 200


def inventory_numbers(start: str, count: int) -> list[str]:
    """`INV-009`, 3 -> `INV-009`, `INV-010`, `INV-011` (zero padding kept)."""
    if count == 1:
        return [start]
    match = re.search(r"(\d+)$", start)
    if not match:
        raise serializers.ValidationError(
            {"inventar_raqami": "Bir nechta nusxa uchun inventar raqami raqam bilan tugashi kerak (masalan, INV-001)."}
        )
    prefix, digits = start[: match.start()], match.group(1)
    first = int(digits)
    return [f"{prefix}{str(first + i).zfill(len(digits))}" for i in range(count)]


class NusxaYaratishSerializer(TenantSerializerMixin, serializers.ModelSerializer):
    """POST /api/copies/ — one copy, or `count` copies with consecutive inventory numbers."""

    count = serializers.IntegerField(
        write_only=True, required=False, default=1, min_value=1, max_value=MAX_COPIES_PER_REQUEST
    )

    class Meta:
        model = Nusxa
        fields = ["id", "kitob", "inventar_raqami", "javon", "qabul_sana", "izoh", "count"]
        read_only_fields = ["id"]
        # Received date defaults to today when the client omits it.
        extra_kwargs = {"qabul_sana": {"required": False}}

    def validate(self, attrs):
        numbers = inventory_numbers(attrs["inventar_raqami"], attrs.get("count", 1))
        # Unique per organization; `organization` is not a serializer field,
        # so DRF would not catch this and the DB constraint would raise a 500.
        org = self._organization()
        if org is not None:
            taken = list(
                Nusxa.objects.filter(organization=org, inventar_raqami__in=numbers)
                .values_list("inventar_raqami", flat=True)[:5]
            )
            if taken:
                raise serializers.ValidationError(
                    {"inventar_raqami": "Bu inventar raqami allaqachon mavjud: " + ", ".join(taken)}
                )
        attrs["inventory_numbers"] = numbers
        return attrs

    def create(self, validated_data):
        validated_data.pop("count", None)
        numbers = validated_data.pop("inventory_numbers")
        validated_data.setdefault("holati", "mavjud")
        validated_data.setdefault("qabul_sana", timezone.localdate())
        with transaction.atomic():
            created = [Nusxa.objects.create(**{**validated_data, "inventar_raqami": n}) for n in numbers]
        self.created_count = len(created)
        return created[0]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["created_count"] = getattr(self, "created_count", 1)
        return data
