"""Botning sozlamalari. .env faylini loyihaning ildizidan (Kutubxona/.env) o'qiydi."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_REDIS = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
FSM_REDIS_URL = os.environ.get("BOT_FSM_REDIS_URL", _REDIS.rsplit("/", 1)[0] + "/2")
API_BASE_URL = os.environ.get("BOT_API_BASE_URL", "http://127.0.0.1:8000/api")

# Webhook mode: Telegram posts updates to BOT_WEBHOOK_URL (proxied by nginx to
# BOT_WEBHOOK_HOST:BOT_WEBHOOK_PORT). Empty URL keeps the old long polling.
WEBHOOK_URL = os.environ.get("BOT_WEBHOOK_URL", "").strip()
WEBHOOK_SECRET = os.environ.get("BOT_WEBHOOK_SECRET", "").strip()
WEBHOOK_HOST = os.environ.get("BOT_WEBHOOK_HOST", "127.0.0.1")
WEBHOOK_PORT = int(os.environ.get("BOT_WEBHOOK_PORT", "8081"))

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