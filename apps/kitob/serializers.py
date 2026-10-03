from rest_framework import serializers
from kitob.models import BandQilish, Kitob


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
            "til",
            "narh",
            "buyurtma_soni",
            "holati",
            "nashr_yili",
            "nashriyot",
            "tavsif",
            "qoshilgan_sana",
        ]
        # `holati` kitob holatidan emas, nusxalar (va «asli» berish yozuvi)
        # holatidan `kitob_holatini_yenila()` orqali hisoblanadi. Shu holatni
        # qo'lda o'zgartirish mumkin bo'lmasa, kitob ro'yxatida «Mavjud» deb
        # turib, aslida berilgan bo'lishi yoki keyingi berishda
        # IntegrityError chiqishi mumkin.
        read_only_fields = ["id", "qoshilgan_sana", "holati"]

    def validate_isbn(self, value):
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
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
    faol_navbatlar = serializers.IntegerField(read_only=True)

    class Meta:
        model = Kitob
        fields = [
            "id",
            "nomi",
            "muallif",
            "isbn",
            "janr",
            "til",
            "narh",
            "buyurtma_soni",
            "holati",
            "nashr_yili",
            "nashriyot",
            "tavsif",
            "qoshilgan_sana",
"mavjud_nusxalar",
            "jami_nusxalar",
            "faol_navbatlar",
        ]


class BandQilishSerializer(serializers.ModelSerializer):
    """Band qilish so'rovi (kutubxonachi paneli va bot uchun)."""

    kitob_nomi = serializers.CharField(source="kitob.nomi", read_only=True)
    kitob_muallif = serializers.CharField(source="kitob.muallif", read_only=True)
    oquvchi_fish = serializers.CharField(source="oquvchi.fish", read_only=True)
    oquvchi_rol = serializers.CharField(source="oquvchi.rol", read_only=True)
    oquvchi_sinf = serializers.SerializerMethodField()
    tasdiqlovchi_fish = serializers.CharField(
        source="tasdiqlovchi.get_full_name", read_only=True, default=""
    )

    class Meta:
        model = BandQilish
        fields = [
            "id",
            "kitob",
            "kitob_nomi",
            "kitob_muallif",
            "oquvchi",
            "oquvchi_fish",
            "oquvchi_rol",
            "oquvchi_sinf",
            "holati",
            "izoh",
            "so_rov_sanasi",
            "tasdiqlovchi",
            "tasdiqlovchi_fish",
            "tasdiqlash_sanasi",
            "tasdiqlash_izohi",
            "berish",
        ]
        read_only_fields = fields

    def get_oquvchi_sinf(self, obj):
        if obj.oquvchi.rol == "oqituvchi":
            return obj.oquvchi.kasb or ""
        return obj.oquvchi.sinf or ""


class BandQilishYaratishSerializer(serializers.Serializer):
    """POST /api/books/{id}/hold/ — kitobni band qilish so'rovi.

    Bot `telegram_id` orqali, veb-panel esa `oquvchi` (PK) orqali yuboradi.
    So'rov yaratilgandan keyin kitob tasdiqlanmaguncha hech kimga
    berilmaydi (`berish/services.py::kitob_ber`).
    """

    oquvchi = serializers.IntegerField(required=False)
    telegram_id = serializers.IntegerField(required=False)
    izoh = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate(self, attrs):
        from oquvchi.models import Oquvchi

        if not attrs.get("oquvchi") and not attrs.get("telegram_id"):
            raise serializers.ValidationError(
                {"error": "oquvchi_kerak", "detail": "oquvchi yoki telegram_id kiritilishi shart"}
            )
        if attrs.get("oquvchi"):
            oquvchi = Oquvchi.objects.filter(pk=attrs["oquvchi"]).first()
        else:
            oquvchi = Oquvchi.objects.filter(telegram_id=attrs["telegram_id"]).first()
        if not oquvchi:
            raise serializers.ValidationError(
                {"error": "oquvchi_topilmadi", "detail": "O'quvchi topilmadi yoki bog'lanmagan"}
            )
        attrs["oquvchi"] = oquvchi
        return attrs


class BandQilishTasdiqSerializer(serializers.Serializer):
    """POST /api/holds/{id}/approve|reject/ — {"izoh": "..."} (ixtiyoriy)."""

    izoh = serializers.CharField(required=False, allow_blank=True, max_length=255)


class BandQilishMeniSerializer(serializers.ModelSerializer):
    """GET /api/holds/my/?telegram_id= — o'quvchining band so'rovlari."""

    kitob_nomi = serializers.CharField(source="kitob.nomi", read_only=True)
    kitob_muallif = serializers.CharField(source="kitob.muallif", read_only=True)

    class Meta:
        model = BandQilish
        fields = [
            "id",
            "kitob",
            "kitob_nomi",
            "kitob_muallif",
            "holati",
            "izoh",
            "so_rov_sanasi",
            "tasdiqlash_sanasi",
            "tasdiqlash_izohi",
        ]
        read_only_fields = fields