from rest_framework import serializers
from jarima.models import Jarima



class JarimaSerializer(serializers.ModelSerializer):

    oquvchi_fish = serializers.CharField(source="berish.oquvchi.fish", read_only=True)
    oquvchi_id = serializers.IntegerField(source="berish.oquvchi_id", read_only=True)
    oquvchi_telefon = serializers.CharField(source="berish.oquvchi.telefon", read_only=True)
    oquvchi_sinf = serializers.SerializerMethodField()
    kitob_nomi = serializers.CharField(source="berish.kitob.nomi", read_only=True)

    def get_oquvchi_sinf(self, obj):
        o = obj.berish.oquvchi
        return (f"{o.sinf}-sinf" if o.sinf else "") or o.kasb or ""

    class Meta:
        model = Jarima
        fields = [
            "id",
            "berish",
            "oquvchi_id",
            "oquvchi_fish",
            "oquvchi_telefon",
            "oquvchi_sinf",
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