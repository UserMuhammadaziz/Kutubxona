"""Bot xizmat (service) akkauntini yaratish / tiklash buyrug'i.

Ishlatish:
    python manage.py seed_service_account

Bu buyruq bot/config.py bilan bir xil usulda loyiha ildizidagi .env faylini
o'qiydi va undagi BOT_SERVICE_USERNAME / BOT_SERVICE_PASSWORD qiymatlariga mos
keladigan faol xizmat foydalanuvchisini yaratadi yoki tiklaydi.

Nega kerak:
  Django API ishlab chiqish uchun `user` app'dagi IsLibrarian/IsAuthenticated
  ruxsatlariga ega User akkauntlari qo'llaniladi. Bot esa `bot/api_client.py`
  orqali .env'dan username/password olib, `/api/auth/token/` ga JWT so'rov
  yuboradi. Agar ushbu akkaunt mavjud bo'lmasa yoki is_active=False bo'lsa yoki
  parol noto'g'ri bo'lsa — bot "Bot xizmat akkauntiga kirib bo'lmadi" xatosini
  qaytaradi (JWT login "No active account found with the given credentials").

Holatlar:
  - Akkaunt yo'q       -> is_active=True, to'g'ri parol bilan yaratadi
  - Akkaunt nofaol     -> is_active=True qiladi
  - Parol noto'g'ri    -> set_password bilan o'rnatadi (JWT login tuzaladi)
  - BOT_SERVICE_* .env da yo'q -> CommandError (XATO ma'lumot bilan)
"""
import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from dotenv import load_dotenv

User = get_user_model()


class Command(BaseCommand):
    help = (
        "BOT_SERVICE_USERNAME/PASSWORD (.env) bilan bot uchun xizmat akkauntini "
        "yaratadi yoki tiklaydi."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default=None,
            help="Foydalanuvchi nomi (standart: .env BOT_SERVICE_USERNAME)",
        )
        parser.add_argument(
            "--password",
            type=str,
            default=None,
            help="Parol (standart: .env BOT_SERVICE_PASSWORD)",
        )

    def handle(self, *args, **options):
        # bot/config.py bilan bir xil: .env ni loyiha ildizidan o'qish.
        BASE_DIR = Path(settings.BASE_DIR)
        load_dotenv(BASE_DIR / ".env")

        username = options["username"] or os.environ.get(
            "BOT_SERVICE_USERNAME", ""
        )
        password = options["password"] or os.environ.get(
            "BOT_SERVICE_PASSWORD", ""
        )

        if not username:
            raise CommandError(
                "BOT_SERVICE_USERNAME .env faylida topilmadi. "
                "--username orqali bering."
            )
        if not password:
            raise CommandError(
                "BOT_SERVICE_PASSWORD .env faylida topilmadi. "
                "--password orqali bering."
            )

        user, yaratildi = User.objects.get_or_create(
            username=username,
            defaults=dict(is_active=True),
        )

        amallar = []
        if yaratildi:
            amallar.append("yaratildi")

        if not user.is_active:
            user.is_active = True
            amallar.append("aktivlashtirildi")

        # Parolni set_password bilan o'rnatamiz — shu orqali JWT login (parol
        # tekshiruvi) to'g'ri ishlaydi (AbstractUser default parolga ega bo'lishi
        # shart emas, set_password hashlab saqlaydi).
        user.set_password(password)
        user.save(update_fields=["password", "is_active"])
        amallar.append("parol tiklandi")

        self.stdout.write(
            self.style.SUCCESS(
                f"Bot xizmat akkaunti: '{user.username}' "
                f"(is_active={user.is_active}) — " + ", ".join(amallar)
            )
        )
