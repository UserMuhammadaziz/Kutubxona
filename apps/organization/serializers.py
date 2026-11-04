from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import AuditLog, Membership, Organization, SubscriptionPlan
from .services import subscription_for
from .tenancy import foydalanuvchi_azoligi

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    rol = serializers.SerializerMethodField()
    obuna = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "nomi",
            "slug",
            "turi",
            "tavsif",
            "telefon",
            "email",
            "manzil",
            "logo_url",
            "faol",
            "status",
            "status_reason",
            "status_changed_at",
            "approved_at",
            "muddat_kun",
            "kunlik_jarima",
            "limit_kitob",
            "taklif_soat",
            "eslatma_kunlar_oldin",
            "kitob_xabarlari_yoqilgan",
            "yaratilgan",
            "rol",
            "obuna",
        ]
        read_only_fields = [
            "id",
            "slug",
            "faol",
            "status",
            "status_reason",
            "status_changed_at",
            "approved_at",
            "yaratilgan",
            "rol",
            "obuna",
        ]

    def get_rol(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        if request.user.is_superuser:
            return "administrator"
        azolik = foydalanuvchi_azoligi(request.user, obj)
        return azolik.rol if azolik else None

    def get_obuna(self, obj):
        obuna = subscription_for(obj)
        return {
            "plan": obuna.plan.code,
            "plan_nomi": obuna.plan.nomi,
            "status": obuna.samarali_holat,
            "trial_ends_at": obuna.trial_ends_at,
            "current_period_end": obuna.current_period_end,
            "limits": {
                "max_staff": obuna.plan.max_staff,
                "max_resources": obuna.plan.max_resources,
                "max_customers": obuna.plan.max_customers,
            },
        }

    def validate_slug(self, value):
        value = slugify(value)
        if not value:
            raise serializers.ValidationError("Slug bo'sh bo'lishi mumkin emas.")
        return value


class SaaSOrganizationSerializer(OrganizationSerializer):
    """Platforma administratori uchun kengaytirilgan ko'rinish."""

    egasi_username = serializers.CharField(source="egasi.username", read_only=True)
    egasi_ismi = serializers.CharField(source="egasi.full_name", read_only=True)
    azoliklar_soni = serializers.SerializerMethodField()
    reyting = serializers.SerializerMethodField()
    telegram_bot_status = serializers.SerializerMethodField()

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + [
            "egasi_username",
            "egasi_ismi",
            "azoliklar_soni",
            "reyting",
            "telegram_bot_status",
        ]

    def get_azoliklar_soni(self, obj):
        return obj.a_zolar.filter(faol=True).count()

    def get_reyting(self, obj):
        """Tashkilot reytingi ma'lumotlari."""
        from stats.models import LibraryRating, LibraryActivityRating
        
        # Asosiy LibraryRating - o'quvchilar tomonidan berilgan baholar
        lr = LibraryRating.objects.filter(organization=obj).first()
        # Faollik reytingi (LibraryActivityRating)
        lar = LibraryActivityRating.objects.filter(organization=obj).first()
        
        # O'quvchilar ortalamasi bahosi
        if lr:
            # Baholar massivini o'qib averages hisoblash
            from django.db.models import Avg
            avg_baho = LibraryRating.objects.filter(organization=obj).aggregate(
                Avg("baho")
            )["baho__avg"]
            ortacha_baho = float(avg_baho) if avg_baho else 0
            baho_soni = LibraryRating.objects.filter(organization=obj).count()
        else:
            ortacha_baho = 0
            baho_soni = 0
        
        # Faollik reytingi ma'lumotlari
        if lar:
            umumiy_bali = float(lar.umumiy_bali)
            faol_oquvchi_soni = lar.faol_oquvchi_soni
            berishlar_soni = lar.berishlar_soni
        else:
            umumiy_bali = 0
            faol_oquvchi_soni = 0
            berishlar_soni = 0
        
        return {
            "ortacha_baho": ortacha_baho,
            "baho_soni": baho_soni,
            "umumiy_bali": umumiy_bali,
            "faol_oquvchi_soni": faol_oquvchi_soni,
            "berishlar_soni": berishlar_soni,
        }

    def get_telegram_bot_status(self, obj):
        """Telegram bot holati."""
        bot = getattr(obj, "telegram_bot", None)
        if bot is None:
            return {
                "status": "yok",
                "username": "",
                "holati_matn": "boti_yok",
            }
        # Holarning matn qiymatini olish
        holat_map = dict(Organization.HOLAT_CHOICES)
        holati_matn = holat_map.get(bot.holati, bot.holati)
        return {
            "status": bot.holati,
            "holati_matn": holati_matn,
            "username": bot.username,
        }


class MembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    telefon = serializers.CharField(source="user.telefon", read_only=True)
    organization_nomi = serializers.CharField(source="organization.nomi", read_only=True)

    class Meta:
        model = Membership
        fields = [
            "id",
            "organization",
            "organization_nomi",
            "user_id",
            "username",
            "full_name",
            "telefon",
            "rol",
            "faol",
            "telegram_id",
            "qoshilgan",
        ]
        read_only_fields = ["id", "organization", "user_id", "username", "full_name", "telefon", "qoshilgan"]


class RegisterSerializer(serializers.Serializer):
    """Ochiq ro'yxatdan o'tish: foydalanuvchi + PENDING tashkilot arizasi.

    Tashkilot darhol faol bo'lmaydi — platforma administratori tasdiqlashi
    kerak. Tasdiqlangunga qadar tenant ma'lumotlariga kirish yopiq.
    """

    kutubxona_nomi = serializers.CharField(max_length=160)
    slug = serializers.SlugField(max_length=80, required=False, allow_blank=True)
    turi = serializers.ChoiceField(
        choices=Organization.TURI_CHOICES, required=False, default="library"
    )
    tavsif = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    full_name = serializers.CharField(max_length=120)
    username = serializers.CharField(max_length=150)
    telefon = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    def validate_username(self, value):
        value = value.strip()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Bu login allaqachon band.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Parollar mos emas."})
        from django.contrib.auth.password_validation import validate_password

        validate_password(attrs["password"])
        return attrs

    def _slug(self, nomi, slug):
        asos = slugify(slug or nomi) or "kutubxona"
        nomzod = asos
        i = 2
        while Organization.objects.filter(slug=nomzod).exists():
            nomzod = f"{asos}-{i}"
            i += 1
        return nomzod

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        organization = Organization.objects.create(
            nomi=validated_data["kutubxona_nomi"],
            slug=self._slug(validated_data["kutubxona_nomi"], validated_data.get("slug")),
            turi=validated_data.get("turi", "library"),
            tavsif=validated_data.get("tavsif", ""),
            telefon=validated_data.get("telefon", ""),
            email=validated_data.get("email", ""),
            status=Organization.HOLAT_PENDING,
            egasi=None,
        )
        user = User.objects.create_user(
            username=validated_data["username"].strip(),
            password=password,
            full_name=validated_data["full_name"].strip(),
            telefon=validated_data.get("telefon", ""),
            email=validated_data.get("email", ""),
            rol="administrator",
        )
        organization.egasi = user
        organization.save(update_fields=["egasi", "faol"])
        Membership.objects.create(
            organization=organization, user=user, rol="egasi", faol=True
        )
        subscription_for(organization, trial=True)
        from .services import log_action

        log_action(
            "organization.registration_requested",
            actor=user,
            organization=organization,
            target_type="organization",
            target_id=organization.pk,
            metadata={
                "nomi": organization.nomi,
                "turi": organization.turi,
                "email": organization.email,
            },
        )
        refresh = RefreshToken.for_user(user)
        return {
            "organization": organization,
            "user": user,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "code",
            "nomi",
            "tavsif",
            "narx_oylik",
            "max_staff",
            "max_resources",
            "max_customers",
            "xususiyatlar",
            "tartib",
            "faol",
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True)
    organization_nomi = serializers.CharField(
        source="organization.nomi", read_only=True
    )

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "organization",
            "organization_nomi",
            "actor",
            "actor_username",
            "action",
            "target_type",
            "target_id",
            "metadata",
            "ip_address",
            "yaratilgan",
        ]


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        from django.contrib.auth.password_validation import validate_password

        validate_password(attrs["password"])
        return attrs
