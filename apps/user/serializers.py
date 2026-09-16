# apps/user/serializers.py
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Kutubxonachi / administrator xodimini ko'rsatish uchun."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "rol",
            "telefon",
            "is_active",
        ]
        read_only_fields = ["id"]


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

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user