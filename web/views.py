import hashlib
import json
import logging
import os
from pathlib import Path

from django.core.cache import cache
from django.http import FileResponse, Http404
from django.views import View
from django.views.generic import TemplateView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    from google.api_core.exceptions import ResourceExhausted
except ImportError:
    genai = None
    ResourceExhausted = type("ResourceExhausted", (Exception,), {})

# PWA service worker (frontend/public/sw.js dan Vite build qiladi).
SW_FILE = Path(__file__).resolve().parent.parent / "web" / "static" / "web" / "dist" / "sw.js"


def service_worker(request):
    """Service worker'ni ildiz manzildan (`/sw.js`) beradi.

    U `static/` ostida emas, aynan `/sw.js` da bo'lishi shunki SW scope'i
    fayl joylashgan papkadan boshlanadi: `/static/web/dist/sw.js` faqat
    `/static/web/dist/` sahifalarini boshqarardi, `/sw.js` esa butun ilovani.
    """
    if not SW_FILE.is_file():
        raise Http404("sw.js topilmadi (avval `npm run build` bajarilsin)")
    response = FileResponse(open(SW_FILE, "rb"), content_type="application/javascript")
    response["Cache-Control"] = "no-cache"
    return response



SYSTEM_PROMPT = (
    "Sen tuman kutubxonasi boshqaruv tizimining yordamchisisan. Kutubxonachiga "
    "kitob berish/qaytarish, band qilish, navbat, jarima va o'quvchilar bilan "
    "ishlashda yordam ber. Faqat o'zbek tilida, qisqa va aniq javob ber. "
    "Tizimdagi aniq ma'lumotlarni (kim qaysi kitobni olgan va h.k.) bilmaysan — "
    "o'ylab topma, kerakli bo'limga yo'nalt."
)
MAX_MESSAGE_LEN = 2000
MAX_HISTORY = 20


class ChatbotThrottle(UserRateThrottle):
    scope = "chatbot"


def _clean_history(raw) -> list[dict]:
    """Klient yuborgan tarixdan faqat xavfsiz `user`/`model` matnlarini oladi."""
    clean = []
    if not isinstance(raw, list):
        return clean
    for item in raw[-MAX_HISTORY:]:
        if not isinstance(item, dict) or item.get("role") not in ("user", "model"):
            continue
        parts = item.get("parts")
        if not isinstance(parts, list) or not all(isinstance(x, str) for x in parts):
            continue
        clean.append({"role": item["role"], "parts": [x[:MAX_MESSAGE_LEN] for x in parts]})
    return clean


class ChatbotView(APIView):
    """Gemini API proxy: faqat tizimga kirgan xodimlar uchun."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ChatbotThrottle]

    def post(self, request):
        if genai is None:
            return Response({"error": "AI xizmati o'rnatilmagan"}, status=503)
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return Response({"error": "AI xizmati sozlanmagan"}, status=503)

        message = request.data.get("message")
        if not isinstance(message, str) or not message.strip():
            return Response({"error": "Xabar bo'sh bo'lmasligi kerak"}, status=400)
        message = message.strip()
        if len(message) > MAX_MESSAGE_LEN:
            return Response({"error": f"Xabar {MAX_MESSAGE_LEN} belgidan oshmasin"}, status=400)

        # Tarixsiz (yangi suhbat) bir xil savol — Gemini kvotasini tejash uchun keshlanadi.
        history = _clean_history(request.data.get("history"))
        kalit = None
        if not history:
            kalit = "chatbot:" + hashlib.sha256(message.lower().encode()).hexdigest()
            if (kesh := cache.get(kalit)) is not None:
                return Response(
                    {
                        "response": kesh,
                        "history": [
                            {"role": "user", "parts": [message]},
                            {"role": "model", "parts": [kesh]},
                        ],
                    }
                )

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                os.environ.get("GEMINI_MODEL", "gemini-flash-latest"),
                system_instruction=SYSTEM_PROMPT,
            )
            chat = model.start_chat(history=history)
            text = chat.send_message(message).text
        except ResourceExhausted:
            logger.warning("Gemini kvotasi tugagan")
            return Response({"error": "AI limiti tugadi. Keyinroq urinib ko'ring."}, status=429)
        except Exception:
            logger.exception("Gemini so'rovi muvaffaqiyatsiz")
            return Response({"error": "AI hozir javob bera olmadi. Keyinroq urinib ko'ring."}, status=502)

        if kalit:
            cache.set(kalit, text, 3600)
        return Response(
            {
                "response": text,
                "history": [
                    {"role": "user", "parts": [message]},
                    {"role": "model", "parts": [text]},
                ],
            }
        )


COMMAND_PROMPT = """Siz kutubxonachi yordamchisi (Librarian AI Copilot) tizimisiz.
Vazifangiz — kutubxonachining o'zbek tilidagi buyrug'ini frontend bajarishi uchun JSON amalga aylantirish.

Action turlari va payload kalitlari:
- SEARCH_READER: {"query": "ism, telefon, sinf yoki karta raqami"}
- SEARCH_BOOK: {"query": "nomi, muallifi yoki inventar raqami"}
- ISSUE_BOOK: {"reader_query": "ism familiya (sinf bo'lsa qo'shib)", "book_title": "kitob nomi"}
- RETURN_BOOK: {"inventory_number": "nusxa inventar raqami", "reader_query": "kitobxon ismi"} (bittasi yetarli)
- APPROVE_HOLD: {}
- SHOW_OVERDUE: {}
- UNKNOWN: {}

Faqat JSON obyekt qaytaring, ortiqcha so'z yoki markdown yo'q:
{"action": "<ACTION>", "payload": {...}, "summary": "1 jumlalik qisqa status"}
Topilmagan parametrni payload'ga qo'shmang. O'ylab topmang."""

COMMAND_ACTIONS = {
    "SEARCH_READER": ("query",),
    "SEARCH_BOOK": ("query",),
    "ISSUE_BOOK": ("reader_query", "book_title"),
    "RETURN_BOOK": ("inventory_number", "reader_query"),
    "APPROVE_HOLD": (),
    "SHOW_OVERDUE": (),
    "UNKNOWN": (),
}
MAX_COMMAND_LEN = 300


def normalize_command(raw: str) -> dict:
    """Model javobini tekshiradi: faqat ruxsat etilgan action va payload kalitlari qoladi."""
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        data = None
    unknown = {"action": "UNKNOWN", "payload": {}, "summary": "Buyruq tushunarsiz. Qayta aytib ko'ring."}
    if not isinstance(data, dict) or data.get("action") not in COMMAND_ACTIONS:
        return unknown
    action = data["action"]
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    clean = {
        k: v.strip()[:100]
        for k, v in payload.items()
        if k in COMMAND_ACTIONS[action] and isinstance(v, str) and v.strip()
    }
    summary = data.get("summary") if isinstance(data.get("summary"), str) else ""
    return {"action": action, "payload": clean, "summary": summary.strip()[:200]}


class LibrarianCommandView(APIView):
    """Kutubxonachi buyrug'ini (Ctrl+K) JSON action'ga aylantiradi. Amalni frontend bajaradi."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ChatbotThrottle]

    def post(self, request):
        if genai is None:
            return Response({"error": "AI xizmati o'rnatilmagan"}, status=503)
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return Response({"error": "AI xizmati sozlanmagan"}, status=503)

        prompt = request.data.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            return Response({"error": "Buyruq bo'sh bo'lmasligi kerak"}, status=400)
        prompt = prompt.strip()
        if len(prompt) > MAX_COMMAND_LEN:
            return Response({"error": f"Buyruq {MAX_COMMAND_LEN} belgidan oshmasin"}, status=400)

        kalit = "aicmd:" + hashlib.sha256(prompt.lower().encode()).hexdigest()
        if (kesh := cache.get(kalit)) is not None:
            return Response(kesh)

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                os.environ.get("GEMINI_MODEL", "gemini-flash-latest"),
                system_instruction=COMMAND_PROMPT,
                generation_config={"response_mime_type": "application/json", "temperature": 0},
            )
            raw = model.generate_content(prompt).text
        except ResourceExhausted:
            logger.warning("Gemini kvotasi tugagan")
            return Response({"error": "AI limiti tugadi. Keyinroq urinib ko'ring."}, status=429)
        except Exception:
            logger.exception("Gemini buyruq so'rovi muvaffaqiyatsiz")
            return Response({"error": "AI hozir javob bera olmadi. Keyinroq urinib ko'ring."}, status=502)

        natija = normalize_command(raw)
        if natija["action"] != "UNKNOWN":
            cache.set(kalit, natija, 600)
        return Response(natija)


class IndexView(TemplateView):
    """Admin panelning yagona HTML sahifasi (React SPA shell).

    Sahifa frontend/ papkasida React + TypeScript bilan qurilgan va
    `npm run build` orqali web/static/web/dist/ ga build qilinadi. Ushbu
    build chiqargan index.html shu joyga (web/templates/web/index.html)
    qo'lda ko'chiriladi. Barcha ma'lumotlar shu SPA ichidagi JS orqali
    /api/ endpointlaridan olinadi, JWT tokenlar localStorage'da saqlanadi.
    Client-side routing (React Router) ishlashi uchun web/urls.py barcha
    admin/ va api/ bo'lmagan yo'llarni shu view'ga yo'naltiradi."""

    template_name = "web/index.html"
