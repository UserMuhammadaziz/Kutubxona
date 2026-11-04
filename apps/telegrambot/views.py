import hmac
import json
import logging

from django.db import IntegrityError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from organization.tenancy import joriy_kutubxonani_aniqla
from user.permissions import IsAdmin

from .client import TelegramAPIError
from .models import TelegramBot, TelegramUpdate
from .serializers import TelegramBotSerializer
from .services import (
    botni_ol,
    botni_tekshirish,
    botni_ulash,
    botni_uzish,
    webhookni_qayta_ornat,
    yangilanishni_qabul_qil,
)

logger = logging.getLogger(__name__)


class WebhookThrottle(AnonRateThrottle):
    scope = "bot_webhook"


@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(APIView):
    """Telegram webhook.

    Kutubxona `webhook_path` (opaque) orqali aniqlanadi. Telegram yuborgan
    `X-Telegram-Bot-Api-Secret-Token` sarlavhasi bazadagi secret bilan
    solishtiriladi. Message/callback ichidagi hech qanday ID'ga ishonilmaydi.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [WebhookThrottle]

    def post(self, request, path):
        bot = (
            TelegramBot.objects.select_related("organization")
            .filter(webhook_path=path)
            .first()
        )
        if not bot:
            return Response({"detail": "topilmadi"}, status=status.HTTP_404_NOT_FOUND)
        kelgan_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(kelgan_secret, bot.webhook_secret):
            return Response({"detail": "ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)
        if not bot.organization.faol or bot.holati != "ulangan":
            return Response({"ok": True})

        try:
            update = json.loads(request.body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return Response({"detail": "noto'g'ri json"}, status=400)
        update_id = update.get("update_id")
        if update_id is None:
            return Response({"ok": True})
        try:
            TelegramUpdate.objects.create(bot=bot, update_id=int(update_id))
        except (IntegrityError, ValueError):
            return Response({"ok": True})

        try:
            yangilanishni_qabul_qil(bot, update)
        except Exception:  # pragma: no cover - Telegram 200 kutadi
            logger.exception("Telegram update xatosi (bot=%s, update=%s)", bot.pk, update_id)
        return Response({"ok": True})


class TelegramBotViewSetMixin:
    permission_classes = [IsAdmin]

    def get_organization(self):
        return joriy_kutubxonani_aniqla(self.request, required=True)

    def get_bot(self):
        bot = botni_ol(self.get_organization())
        if not bot:
            return None
        return bot


class TelegramBotSettingsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        org = joriy_kutubxonani_aniqla(request, required=True)
        bot = botni_ol(org)
        if not bot:
            return Response({"ulangan": False})
        return Response(
            {
                "ulangan": bot.holati == "ulangan",
                "bot": TelegramBotSerializer(bot).data,
            }
        )

    def post(self, request):
        org = joriy_kutubxonani_aniqla(request, required=True)
        bot = botni_ulash(org, request.data.get("token", ""))
        return Response(
            {"ulangan": True, "bot": TelegramBotSerializer(bot).data},
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request):
        org = joriy_kutubxonani_aniqla(request, required=True)
        bot = botni_ol(org)
        if bot:
            botni_uzish(bot)
        return Response({"ulangan": False})


class TelegramBotActionView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, action):
        org = joriy_kutubxonani_aniqla(request, required=True)
        bot = botni_ol(org)
        if not bot:
            return Response({"detail": "Bot ulanmagan."}, status=404)
        if action == "test":
            botni_tekshirish(bot)
        elif action == "webhook":
            try:
                webhookni_qayta_ornat(bot)
            except TelegramAPIError as xato:
                return Response({"detail": str(xato)}, status=400)
        else:
            return Response({"detail": "Noma'lum amal."}, status=400)
        return Response({"ulangan": bot.holati == "ulangan", "bot": TelegramBotSerializer(bot).data})
