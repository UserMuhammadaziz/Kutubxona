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

# /qaytar buyrug'i kutubxonachi funksiyasini bajaradi va botning xizmat
# akkaunti orqali `IsLibrarian` endpoint'iga murojaat qiladi. Shu sababli
# uni hamma foydalanuvchiga ochiq qoldirmaslik kerak: bu yerda
# ruxsat etilgan Telegram chat_id lar ro'yxati (vergul bilan ajratiladi).
# Bo'sh bo'lsa /qaytar butunlay o'chiriladi.
BOT_ADMIN_CHAT_IDS = frozenset(
    int(q.strip())
    for q in os.environ.get("BOT_ADMIN_CHAT_IDS", "").split(",")
    if q.strip().lstrip("-").isdigit()
)


def bot_adminmi(chat_id: int) -> bool:
    """Berilgan Telegram foydalanuvchisi /qaytar buyrug'idan foydalana oladimi?"""
    return chat_id in BOT_ADMIN_CHAT_IDS


if not BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN .env faylida topilmadi. Kutubxona/.env faylini tekshiring."
    )