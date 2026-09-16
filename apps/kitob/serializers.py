from rest_framework import serializers
from kitob.models import Kitob


class KitobSerializer(serializers.ModelSerializer):
    """Kitob ro'yxati / yaratish / tahrirlash uchun asosiy serializer."""

    class Meta:
        model = Kitob
        fields = [
            "id",
            "nomi",
            "muallif",
            "isbn",
            "janr",
            "nashr_yili",
            "nashriyot",
            "tavsif",
            "qoshilgan_sana",
        ]
        read_only_fields = ["id", "qoshilgan_sana"]

    def validate_isbn(self, value):
        # unique=True modelda bor, lekin aniq xabar uchun qo'shimcha tekshiruv
        qs = Kitob.objects.filter(isbn=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu ISBN bilan kitob allaqachon mavjud.")
        return value


class NusxaQisqaSerializer(serializers.Serializer):
    """Kitob detail sahifasida nusxalarni ko'rsatish uchun yengil serializer.
    (nusxa/serializers.py dagi to'liq NusxaSerializer bilan aylanma import
    bo'lmasligi uchun bu yerda alohida, yengil versiyasi ishlatiladi.)
    """

    id = serializers.IntegerField()
    inventar_raqami = serializers.CharField()
    holati = serializers.CharField()
    javon = serializers.CharField()


class KitobDetailSerializer(KitobSerializer):
    """GET /api/books/{id}/ — kitob + nusxalari ro'yxati va holatlari."""

    nusxalar = NusxaQisqaSerializer(many=True, read_only=True)

    class Meta(KitobSerializer.Meta):
        fields = KitobSerializer.Meta.fields + ["nusxalar"]


class KitobQidiruvSerializer(serializers.ModelSerializer):
    """GET /api/books/search/?q= — annotate(...) bilan hisoblangan
    mavjud_nusxalar va jami_nusxalar maydonlarini queryset'dan oladi.
    View'da .annotate(mavjud_nusxalar=Count(...), jami_nusxalar=Count(...))
    qilingan bo'lishi shart, aks holda bu maydonlar xato beradi.
    """

    mavjud_nusxalar = serializers.IntegerField(read_only=True)
    jami_nusxalar = serializers.IntegerField(read_only=True)

    class Meta:
        model = Kitob
        fields = [
            "id",
            "nomi",
            "muallif",
            "isbn",
            "janr",
            "nashr_yili",
            "mavjud_nusxalar",
            "jami_nusxalar",
        ]