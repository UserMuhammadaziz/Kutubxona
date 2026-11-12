# apps/user/serializers.py
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Kutubxonachi / administrator xodimini ko'rsatish uchun."""

    kutubxonalar = serializers.SerializerMethodField()
    joriy_rol = serializers.SerializerMethodField()

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
        ]
        read_only_fields = ["id"]

    def get_kutubxonalar(self, obj):
        from organization.models import Membership

        qs = Membership.objects.filter(user=obj, faol=True).select_related("organization")
        return [
            {
                "id": a.organization_id,
                "nomi": a.organization.nomi,
                "slug": a.organization.slug,
                "rol": a.rol,
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