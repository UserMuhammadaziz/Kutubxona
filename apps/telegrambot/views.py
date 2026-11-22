import hmac
import json
import logging

from django.db import IntegrityError
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from config.telegram import telegram_escape, telegram_xabar_yubor
from oquvchi.models import Oquvchi
from oquvchi.utils import sinf_kaliti, sinf_normal
from organization.tenancy import joriy_kutubxonani_aniqla
from user.permissions import IsAdmin, IsLibrarian

from .client import TelegramAPIError
from .models import TelegramBot, TelegramUpdate
from .serializers import TelegramBotSerializer, XabarYuborishSerializer
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


def _sinf_kaliti(sinf):
    """Sinflarni tabiiy tartibda saralash: 7-A, 8-B, 10-A."""
    return sinf_kaliti(sinf)


def _qabul_qiluvchilar(org, rol):
    """Joriy kutubxonadagi faol kitobxonlar (tenant doirasida).

    Eski bot orqali yaratilgan ayrim kitobxonlarda `organization` bo'sh
    qolgan. Baza bitta kutubxonadan iborat bo'lsa, ularni ham qabul
    qiluvchilarga qo'shamiz — aks holda kutubxonachi ularni na ko'radi,
    na xabar yubora oladi. Ko'p kutubxonada bunday qilish xavfsiz emas.
    """
    from organization.tenancy import legacy_rejimmi

    qs = Oquvchi.objects.filter(rol=rol, faol=True)
    if org is None:
        # Ko'p kutubxonada tenant aniqlanmasa, hech kimga xabar yuborilmaydi.
        return qs if legacy_rejimmi() else qs.none()
    from organization.models import Organization

    if Organization.objects.filter(status=Organization.HOLAT_ACTIVE).count() <= 1:
        return qs.filter(Q(organization=org) | Q(organization__isnull=True))
    return qs.filter(organization=org)


class SinflarView(APIView):
    """GET /api/messages/classes/?rol=oquvchi — mavjud sinflar ro'yxati."""

    permission_classes = [IsLibrarian]

    def get(self, request):
        rol = request.query_params.get("rol", "oquvchi")
        if rol not in ("oquvchi", "oqituvchi"):
            rol = "oquvchi"
        org = joriy_kutubxonani_aniqla(request, required=True)
        sinflar = (
            _qabul_qiluvchilar(org, rol)
            .exclude(sinf__isnull=True)
            .exclude(sinf="")
            .values_list("sinf", flat=True)
            .distinct()
        )
        # Bir sinf turli yozilishlarda saqlangan bo'lsa ham bitta ko'rsatiladi.
        kanonik = {sinf_normal(sinf) for sinf in sinflar}
        kanonik.discard("")
        return Response(sorted(kanonik, key=_sinf_kaliti))


class XabarYuborishView(APIView):
    """POST /api/messages/send/ — bitta kitobxon, sinf yoki barcha sinflarga.

    Telegram ID bo'lmagan kitobxonlar hisoblanadi, lekin ularga yuborib
    bo'lmaydi — bu holat `telegramsiz` hisobida qaytariladi.
    """

    permission_classes = [IsLibrarian]

    def post(self, request):
        serializer = XabarYuborishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        org = joriy_kutubxonani_aniqla(request, required=True)
        qs = _qabul_qiluvchilar(org, data["rol"])

        if data["tur"] == "shaxs":
            kitobxon = qs.filter(pk=data["oquvchi"]).first()
            if kitobxon is None:
                raise ValidationError({"oquvchi": "Tanlangan kitobxon topilmadi."})
            qabul_qiluvchilar = [kitobxon]
        elif data["tur"] == "sinf":
            # Tanlangan sinf kanonik ko'rinishda keladi; eski yozilishlar ham
            # shu sinfga tegishli bo'lsa ularga ham xabar yetib borishi kerak.
            kalit = sinf_normal(data["sinf"])
            mos_sinflar = {
                xom for xom in qs.values_list("sinf", flat=True) if sinf_normal(xom) == kalit
            }
            qabul_qiluvchilar = list(qs.filter(sinf__in=mos_sinflar))
            if not qabul_qiluvchilar:
                raise ValidationError({"sinf": "Bu sinfda kitobxon topilmadi."})
        else:
            qabul_qiluvchilar = list(qs)
            if not qabul_qiluvchilar:
                raise ValidationError({"detail": "Xabar yuborish uchun kitobxon yo'q."})

        matn = "📢 <b>Kutubxona xabari</b>\n\n" + telegram_escape(data["matn"])
        yuborildi = 0
        telegramsiz = 0
        xatolik = 0
        for kitobxon in qabul_qiluvchilar:
            if not kitobxon.telegram_id:
                telegramsiz += 1
                continue
            if telegram_xabar_yubor(kitobxon.telegram_id, matn, organization=org):
                yuborildi += 1
            else:
                xatolik += 1

        return Response(
            {
                "jami": len(qabul_qiluvchilar),
                "yuborildi": yuborildi,
                "telegramsiz": telegramsiz,
                "xatolik": xatolik,
            }
        )
