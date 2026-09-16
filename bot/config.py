"""Botning sozlamalari. .env faylini loyihaning ildizidan (Kutubxona/.env) o'qiydi."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API_BASE_URL = os.environ.get("BOT_API_BASE_URL", "http://127.0.0.1:8000/api")

# Bot IsAuthenticated/IsLibrarian talab qiladigan endpointlarga kirishi uchun
# ishlatadigan xizmat akkaunti (Django admin orqali rol="kutubxonachi" bilan
# oldindan yaratilishi kerak).
BOT_SERVICE_USERNAME = os.environ.get("BOT_SERVICE_USERNAME", "")
BOT_SERVICE_PASSWORD = os.environ.get("BOT_SERVICE_PASSWORD", "")

if not BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN .env faylida topilmadi. Kutubxona/.env faylini tekshiring."
    )