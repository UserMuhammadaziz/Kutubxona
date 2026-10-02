from rest_framework import serializers
from jarima.models import Jarima



class JarimaSerializer(serializers.ModelSerializer):

    oquvchi_fish = serializers.CharField(source="berish.oquvchi.fish", read_only=True)
    kitob_nomi = serializers.CharField(source="berish.kitob.nomi", read_only=True)

    class Meta:
        model = Jarima
        fields = [
            "id",
            "berish",
            "oquvchi_fish",
            "kitob_nomi",
            "kechikkan_kunlar",
            "kunlik_stavka",
            "summa",
            "tolandimi",
            "tolangan_sana",
            "qabul_qilgan",
            "eslatma_yuborilgan_sana",
            "yangilangan",
        ]
        # summa va kechikkan_kunlar faqat server (celery / services.py)
        # tomonidan hisoblanadi — API orqali yozib bo'lmaydi.
        read_only_fields = [
            "id",
            "kechikkan_kunlar",
            "summa",
            "tolangan_sana",
            "qabul_qilgan",
            "eslatma_yuborilgan_sana",
            "yangilangan",
        ]


class JarimaTolashSerializer(serializers.Serializer):
    """POST /api/fines/{id}/pay/ — jarimani to'langan deb belgilash.
    tolandimi=True bo'lgan jarimani qayta to'lab bo'lmaydi."""

    def validate(self, attrs):
        jarima: Jarima = self.instance
        if jarima.tolandimi:
            raise serializers.ValidationError(
                {"error": "allaqachon_tolangan", "detail": "Bu jarima allaqachon to'langan"}
            )
        return attrs


class JarimaMeniSerializer(serializers.ModelSerializer):
    """GET /api/fines/my/?telegram_id= — o'quvchining to'lanmagan jarimalari."""

    kitob_nomi = serializers.CharField(source="berish.kitob.nomi", read_only=True)

    class Meta:
        model = Jarima
        fields = ["id", "kitob_nomi", "kechikkan_kunlar", "summa", "tolandimi"]