# apps/user/serializers.py
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from organization.services import check_limit

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Kutubxonachi / administrator xodimini ko'rsatish uchun."""

    kutubxonalar = serializers.SerializerMethodField()
    joriy_rol = serializers.SerializerMethodField()
    is_platform = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "rol",
            "telefon",
            "is_active",
            "kutubxonalar",
            "joriy_rol",
            "is_platform",
        ]
        read_only_fields = ["id"]

    def get_is_platform(self, obj):
        # Platform (master) users manage all organizations from /platform.
        return bool(obj.is_superuser or obj.is_staff)

    def get_kutubxonalar(self, obj):
        from organization.models import Membership

        qs = Membership.objects.filter(user=obj, faol=True).select_related("organization")
        return [
            {
                "id": a.organization_id,
                "nomi": a.organization.nomi,
                "slug": a.organization.slug,
                "rol": a.rol,
                # The client shows the blocking status screen before any tenant request.
                "status": a.organization.status,
            }
            for a in qs
        ]

    def get_joriy_rol(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        org = getattr(request, "organization", None)
        if org is None:
            from organization.tenancy import joriy_kutubxonani_aniqla

            try:
                org = joriy_kutubxonani_aniqla(request, required=False)
            except Exception:
                org = None
        if org is None:
            return None
        from organization.tenancy import foydalanuvchi_azoligi

        azolik = foydalanuvchi_azoligi(obj, org)
        return azolik.rol if azolik else None


class StaffSerializer(UserSerializer):
    """A staff member as seen and edited by one library (`/api/staff/`).

    `rol` and `is_active` describe the membership in the current library, so
    changing them never affects the person's access to another library.
    Personal fields are global and editable only while the account belongs to
    this library alone.
    """

    PERSONAL_FIELDS = ("username", "full_name", "telefon")

    def _organization(self):
        return self.context.get("organization")

    def _membership(self, obj):
        org = self._organization()
        if org is None:
            return None
        return obj.a_zoliklar.filter(organization=org).select_related("organization").first()

    def _is_shared(self, obj):
        return (
            obj.is_superuser
            or obj.is_staff
            or obj.a_zoliklar.exclude(organization=self._organization()).exists()
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        membership = self._membership(instance)
        if membership is not None:
            data["rol"] = (
                "administrator" if membership.rol == "egasi" else membership.rol
            )
            data["joriy_rol"] = membership.rol
            data["is_active"] = instance.is_active and membership.faol
        return data

    def get_kutubxonalar(self, obj):
        org = self._organization()
        rows = super().get_kutubxonalar(obj)
        return rows if org is None else [r for r in rows if r["id"] == org.pk]

    def validate(self, attrs):
        obj = self.instance
        membership = self._membership(obj)
        if membership is None:
            return attrs
        if membership.rol == "egasi":
            for name in ("rol", "is_active"):
                if name in attrs:
                    raise serializers.ValidationError(
                        {name: "Kutubxona egasining roli va holatini o'zgartirib bo'lmaydi."}
                    )
        if self._is_shared(obj):
            for name in self.PERSONAL_FIELDS:
                if name in attrs and attrs[name] != getattr(obj, name):
                    raise serializers.ValidationError(
                        {
                            name: "Bu xodim boshqa joyda ham ishlaydi — shaxsiy "
                            "ma'lumotlarini faqat o'zi o'zgartira oladi."
                        }
                    )
            if attrs.get("is_active") and not obj.is_active:
                raise serializers.ValidationError(
                    {"is_active": "Bu akkaunt platforma tomonidan bloklangan."}
                )
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        membership = self._membership(instance)
        if membership is None:
            return super().update(instance, validated_data)
        is_active = validated_data.pop("is_active", None)
        role = validated_data.pop("rol", None)
        shared = self._is_shared(instance)
        if role is not None:
            membership.rol = role
            if not shared:
                # The global role mirrors the only membership.
                validated_data["rol"] = role
        if is_active is not None:
            if is_active and not membership.faol:
                check_limit(
                    membership.organization,
                    "max_staff",
                    membership.organization.a_zolar.filter(faol=True).count(),
                )
            membership.faol = is_active
            if is_active and not shared:
                # Accounts blocked before blocking became per-library.
                validated_data["is_active"] = True
        membership.save(update_fields=["rol", "faol"])
        return super().update(instance, validated_data)


class UserCreateSerializer(serializers.ModelSerializer):
    """Administrator yangi xodim (kutubxonachi) yaratganda ishlatiladi."""

    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "rol",
            "telefon",
            "is_active",
            "password",
        ]
        read_only_fields = ["id"]

    def validate_username(self, value):
        value = value.strip()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Bu login allaqachon band.")
        return value

    def create(self, validated_data):
        from organization.models import Membership

        organization = validated_data.pop("organization", None)
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        if organization is not None:
            Membership.objects.create(
                organization=organization,
                user=user,
                rol=user.rol if user.rol in ("administrator", "kutubxonachi") else "kutubxonachi",
                faol=True,
            )
        return user


class ProfilniYangilashSerializer(serializers.ModelSerializer):
    """Kutubxonachi o'z shaxsiy ma'lumotlarini tahrirlash uchun (Profil)."""

    class Meta:
        model = User
        fields = ["username", "full_name", "telefon"]
        extra_kwargs = {
            "username": {"required": False},
            "full_name": {"required": False, "allow_blank": True},
            "telefon": {"required": False, "allow_blank": True},
        }

    def validate_username(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Foydalanuvchi nomi bo'sh bo'lishi mumkin emas.")
        qs = User.objects.filter(username__iexact=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Bu login allaqachon band.")
        return value

    def validate_full_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("To'liq ism bo'sh bo'lishi mumkin emas.")
        return value

    def validate_telefon(self, value):
        return (value or "").strip()


class ParolniAlmashtirishSerializer(serializers.Serializer):
    """Kutubxonachi o'z parolini almashtirish uchun (Profil sahifasi)."""

    joriy_parol = serializers.CharField(write_only=True)
    yangi_parol = serializers.CharField(write_only=True, validators=[validate_password])
    yangi_parol_takror = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["yangi_parol"] != attrs["yangi_parol_takror"]:
            raise serializers.ValidationError(
                {"yangi_parol_takror": "Yangi parollar mos kelmadi."}
            )
        if attrs["joriy_parol"] == attrs["yangi_parol"]:
            raise serializers.ValidationError(
                {"yangi_parol": "Yangi parol joriy paroldan farq qilishi kerak."}
            )
        return attrs