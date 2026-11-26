from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    AuditLog,
    IssueReport,
    Membership,
    Organization,
    OrganizationSubscription,
    SubscriptionPlan,
)
from .services import DEFAULT_PLAN_CODE, subscription_for
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
            "capabilities",
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

    @staticmethod
    def _in_range(value, low, high, label):
        if not low <= value <= high:
            raise serializers.ValidationError(f"{label} {low} dan {high} gacha bo'lishi kerak.")
        return value

    def validate_nomi(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Nom kamida 2 ta belgidan iborat bo'lishi kerak.")
        return value

    def validate_muddat_kun(self, value):
        return self._in_range(value, 1, 365, "Qaytarish muddati")

    def validate_kunlik_jarima(self, value):
        return self._in_range(value, 0, 1_000_000, "Kunlik jarima")

    def validate_limit_kitob(self, value):
        return self._in_range(value, 1, 100, "Kitob limiti")

    def validate_taklif_soat(self, value):
        return self._in_range(value, 1, 720, "Taklif muddati (soat)")

    def validate_eslatma_kunlar_oldin(self, value):
        return self._in_range(value, 0, 30, "Eslatma kunlari")

    def validate_logo_url(self, value):
        if value and not value.lower().startswith("https://"):
            raise serializers.ValidationError("Logo manzili https:// bilan boshlanishi kerak.")
        return value

    def validate_capabilities(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Imkoniyatlar obyekt ko'rinishida bo'lishi kerak.")
        unknown = set(value) - set(Organization.CAPABILITY_KEYS)
        if unknown:
            raise serializers.ValidationError(f"Noma'lum imkoniyat: {', '.join(sorted(unknown))}")
        if any(not isinstance(v, bool) for v in value.values()):
            raise serializers.ValidationError("Imkoniyat qiymati true yoki false bo'lishi kerak.")
        # Merge so a partial update does not switch the other capabilities off.
        return {**(self.instance.capabilities if self.instance else {}), **value}

    def update(self, instance, validated_data):
        was_on = instance.has_capability("search_inline")
        instance = super().update(instance, validated_data)
        if instance.has_capability("search_inline") and not was_on:
            self._refresh_bot_webhook(instance)
        return instance

    @staticmethod
    def _refresh_bot_webhook(organization):
        """Telegram only delivers `inline_query` after the webhook is re-registered with it allowed."""
        import logging

        from telegrambot.services import botni_ol, webhookni_qayta_ornat

        bot = botni_ol(organization)
        if bot and bot.holati == "ulangan":
            try:
                webhookni_qayta_ornat(bot)
            except Exception:  # the setting is saved; the librarian can reconnect the bot
                logging.getLogger(__name__).exception("webhook refresh failed (org=%s)", organization.pk)

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

    # Create-only: owner account (created, or reused when the phone already exists).
    owner = serializers.DictField(child=serializers.CharField(allow_blank=True), write_only=True, required=False)

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + [
            "egasi_username",
            "egasi_ismi",
            "azoliklar_soni",
            "reyting",
            "telegram_bot_status",
            "owner",
        ]
        # Platform admin may set the slug; status changes go through the action endpoints.
        read_only_fields = [f for f in OrganizationSerializer.Meta.read_only_fields if f != "slug"]

    def validate_slug(self, value):
        value = super().validate_slug(value)
        qs = Organization.objects.filter(slug=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu slug band.")
        return value

    def validate_owner(self, value):
        if self.instance:
            raise serializers.ValidationError("Egani yangilash bu yerda qo'llab-quvvatlanmaydi.")
        import re

        telefon = (value.get("telefon") or "").strip()
        if not re.fullmatch(r"\+998\d{9}", telefon):
            raise serializers.ValidationError({"telefon": "Telefon +998901234567 formatida bo'lishi kerak."})
        existing = User.objects.filter(username__iexact=telefon).first()
        if not existing:
            if not (value.get("full_name") or "").strip():
                raise serializers.ValidationError({"full_name": "Egasining ismini kiriting."})
            password = value.get("password") or ""
            if len(password) < 8:
                raise serializers.ValidationError({"password": "Parol kamida 8 ta belgidan iborat bo'lishi kerak."})
        return {**value, "telefon": telefon}

    @transaction.atomic
    def create(self, validated_data):
        owner = validated_data.pop("owner", None)
        # Created by the platform admin: active right away (no approval step).
        validated_data["status"] = Organization.HOLAT_ACTIVE
        organization = Organization.objects.create(**validated_data)
        if owner:
            user = User.objects.filter(username__iexact=owner["telefon"]).first()
            if not user:
                user = User.objects.create_user(
                    username=owner["telefon"],
                    password=owner["password"],
                    full_name=owner["full_name"].strip(),
                    telefon=owner["telefon"],
                    email=owner.get("email", ""),
                    rol="administrator",
                )
            organization.egasi = user
            organization.save(update_fields=["egasi", "faol"])
            Membership.objects.get_or_create(
                organization=organization, user=user, defaults={"rol": "egasi", "faol": True}
            )
        subscription_for(organization, trial=True)
        return organization

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
    # Phone is the login: there is no separate username field.
    telefon = serializers.RegexField(
        r"^\+998\d{9}$",
        max_length=20,
        error_messages={"invalid": "Telefon +998901234567 formatida bo'lishi kerak."},
    )
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8, error_messages={"min_length": "Parol kamida 8 ta belgidan iborat bo'lishi kerak."})
    password_confirm = serializers.CharField(write_only=True)

    PAROL_XABARLARI = {
        "password_too_short": "Parol kamida 8 ta belgidan iborat bo'lishi kerak.",
        "password_too_common": "Parol juda oddiy. Boshqa, murakkabroq parol tanlang.",
        "password_entirely_numeric": "Parol faqat raqamlardan iborat bo'lmasligi kerak.",
        "password_too_similar": "Parol telefon yoki ismingizga juda o'xshash.",
    }

    def validate_telefon(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Bu telefon raqami bilan allaqachon ro'yxatdan o'tilgan.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Parollar mos emas."})
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError

        try:
            validate_password(attrs["password"], user=User(username=attrs["telefon"], full_name=attrs["full_name"]))
        except DjangoValidationError as e:
            xabarlar = [self.PAROL_XABARLARI.get(x.code, str(x.message)) for x in e.error_list]
            raise serializers.ValidationError({"password": xabarlar[0]})
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
            username=validated_data["telefon"],
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
    # Optional on create: generated from the name. Fixed afterwards.
    code = serializers.SlugField(max_length=40, required=False)
    organization_count = serializers.SerializerMethodField()
    is_default = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "code",
            "organization_count",
            "is_default",
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

    def get_organization_count(self, obj):
        count = getattr(obj, "organization_count", None)
        return obj.obunalar.count() if count is None else count

    def get_is_default(self, obj):
        return obj.code == DEFAULT_PLAN_CODE

    def validate_nomi(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Tarif nomi kamida 2 ta belgidan iborat bo'lishi kerak.")
        qs = SubscriptionPlan.objects.filter(nomi__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu nomli tarif allaqachon bor.")
        return value

    def validate_narx_oylik(self, value):
        if value < 0:
            raise serializers.ValidationError("Narx manfiy bo'lishi mumkin emas.")
        return value

    def validate_code(self, value):
        if self.instance:
            if value != self.instance.code:
                raise serializers.ValidationError("Tarif kodini o'zgartirib bo'lmaydi.")
        elif SubscriptionPlan.objects.filter(code=value).exists():
            raise serializers.ValidationError("Bu kodli tarif allaqachon bor.")
        return value

    def _validate_limit(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("Limit kamida 1 bo'lishi kerak. Cheksiz bo'lsa bo'sh qoldiring.")
        return value

    validate_max_staff = _validate_limit
    validate_max_resources = _validate_limit
    validate_max_customers = _validate_limit

    def validate_faol(self, value):
        if not value and self.instance and self.instance.code == DEFAULT_PLAN_CODE:
            raise serializers.ValidationError("Boshlang'ich tarifni o'chirib qo'yib bo'lmaydi.")
        return value

    @staticmethod
    def _unique_code(name):
        base = slugify(name)[:34] or "tarif"
        code, n = base, 2
        while SubscriptionPlan.objects.filter(code=code).exists():
            code, n = f"{base}-{n}", n + 1
        return code

    def create(self, validated_data):
        validated_data.setdefault("code", self._unique_code(validated_data["nomi"]))
        if "tartib" not in validated_data:
            last = SubscriptionPlan.objects.order_by("-tartib").values_list("tartib", flat=True).first()
            validated_data["tartib"] = (last or 0) + 1
        return super().create(validated_data)


class SubscriptionChangeSerializer(serializers.Serializer):
    """Platform admin changes an organization's plan, status or period."""

    plan = serializers.SlugField(required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=OrganizationSubscription.HOLAT_CHOICES,
        required=False,
        error_messages={"invalid_choice": "Obuna holati noto'g'ri."},
    )
    trial_ends_at = serializers.DateTimeField(required=False, allow_null=True)
    current_period_end = serializers.DateTimeField(required=False, allow_null=True)


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


class IssueReportSerializer(serializers.ModelSerializer):
    """POST /api/issue-reports/ — accepts client diagnostics, caps their size."""

    MAX_SCREENSHOT = 2_000_000  # chars of data URL
    MAX_ITEMS = 30

    class Meta:
        model = IssueReport
        fields = [
            "id", "category", "module", "message", "page_url", "user_agent",
            "console_errors", "failed_requests", "screenshot", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_screenshot(self, value):
        if value and not value.startswith("data:image/"):
            raise serializers.ValidationError("Skrinshot formati noto'g'ri.")
        if len(value) > self.MAX_SCREENSHOT:
            raise serializers.ValidationError("Skrinshot juda katta.")
        return value

    def _cap(self, value):
        return (value or [])[: self.MAX_ITEMS]

    def validate_console_errors(self, value):
        return self._cap(value)

    def validate_failed_requests(self, value):
        return self._cap(value)
