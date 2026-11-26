import hashlib
import json
import logging
import os
from pathlib import Path

from django.core.cache import cache
from django.http import FileResponse, Http404
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
    """Service worker'ni ildiz manzildan (`/sw.js`) beradi."""
    if not SW_FILE.is_file():
        raise Http404("sw.js topilmadi (avval `npm run build` bajarilsin)")
    response = FileResponse(open(SW_FILE, "rb"), content_type="application/javascript")
    response["Cache-Control"] = "no-cache"
    return response


# --- Sozlamalar va Promptlar ---
DIST_DIR = SW_FILE.parent

# Files from `frontend/public` are copied to the root of `dist` and requested
# from the site root (`/logo.png`, `/landing/x.webp`, `/manifest.json`).
# Without this view the SPA catch-all answered them with index.html.
PUBLIC_FILE_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".json": "application/json",
    ".webmanifest": "application/manifest+json",
    ".txt": "text/plain; charset=utf-8",
    ".xml": "application/xml",
}


def public_file(request, path):
    """Serve a file from the root of the frontend build, never index.html."""
    target = (DIST_DIR / path).resolve()
    if DIST_DIR.resolve() not in target.parents or not target.is_file():
        raise Http404("Fayl topilmadi")
    content_type = PUBLIC_FILE_TYPES.get(target.suffix.lower())
    if content_type is None:
        raise Http404("Fayl topilmadi")
    response = FileResponse(open(target, "rb"), content_type=content_type)
    # manifest.json changes with deploys; images are versioned by name.
    response["Cache-Control"] = "no-cache" if target.suffix == ".json" else "public, max-age=86400"
    return response


def media_logo(request, name):
    """Serve an uploaded organization logo (always our own re-encoded WebP)."""
    from organization.logo import LOGO_NAME, logo_root

    if not LOGO_NAME.fullmatch(name):
        raise Http404("Fayl topilmadi")
    path = logo_root() / name
    if not path.is_file():
        raise Http404("Fayl topilmadi")
    response = FileResponse(open(path, "rb"), content_type="image/webp")
    # The name contains the content hash, so it never changes.
    response["Cache-Control"] = "public, max-age=31536000, immutable"
    response["X-Content-Type-Options"] = "nosniff"
    return response


GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

CHATBOT_SYSTEM_INSTRUCTION = (
    "Siz — «Kutubxona» tuman kutubxonasi boshqaruv tizimining yordamchisiz. "
    "Kutubxonachiga kitob berish/qaytarish, band qilish, navbat, jarima va o'quvchilar bilan "
    "ishlashda yordam bering. Faqat o'zbek tilida, qisqa va aniq javob bering. "
    "Tizimdagi aniq ma'lumotlarni (kim qaysi kitobni olgan va h.k.) bilmaysiz — "
    "o'ylab topmang, kerakli bo'limga yo'naltiring."
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

MAX_MESSAGE_LEN = 2000
MAX_COMMAND_LEN = 300
MAX_HISTORY = 20


def _chat_saqlash(user, savol: str, javob: str) -> None:
    """Savol-javobni faqat statistika va AI'ni yaxshilash uchun yozadi.

    Foydalanuvchiga qaytarilmaydi (GET yo'q); xato chatni buzmasin.
    """
    from user.models import ChatXabar

    try:
        ChatXabar.objects.bulk_create(
            [
                ChatXabar(user=user, rol="user", matn=savol),
                ChatXabar(user=user, rol="model", matn=javob),
            ]
        )
    except Exception:
        logger.exception("Chat tarixini saqlab bo'lmadi")


PAGE_HINTS = {
    "/loans": "Berish / Qaytarish sahifasi",
    "/readers": "O'quvchilar ro'yxati",
    "/books": "Kitoblar katalogi",
    "/fines": "Jarimalar sahifasi",
    "/announcements": "E'lonlar (ommaviy Telegram xabar) sahifasi",
}


def build_context(request, message: str, page: str = "") -> str:
    """Looks up facts in the user's own library that the message mentions.

    Simple keyword search (no embeddings): books by title/author/ISBN, readers
    by name, plus headline numbers. Everything is scoped to the user's
    organization, so one library never sees another's data.
    """
    from datetime import date

    from django.db.models import Q

    from berish.models import Berish
    from kitob.models import Kitob
    from nusxa.models import Nusxa
    from organization.tenancy import joriy_kutubxonani_aniqla, scope
    from oquvchi.models import Oquvchi

    try:
        org = joriy_kutubxonani_aniqla(request, required=False)
    except Exception:
        return ""
    if org is None:
        return ""

    lines = []
    hint = next((v for k, v in PAGE_HINTS.items() if page.startswith(k)), "")
    if hint:
        lines.append(f"Foydalanuvchi hozir: {hint}.")

    words = [w for w in message.replace("?", " ").replace(",", " ").split() if len(w) >= 4][:6]
    if words:
        q = Q()
        for w in words:
            q |= Q(nomi__icontains=w) | Q(muallif__icontains=w) | Q(isbn__icontains=w)
        for book in scope(Kitob.objects.all(), org).filter(q)[:5]:
            free = Nusxa.objects.filter(kitob=book, holati="mavjud").count()
            total = Nusxa.objects.filter(kitob=book).count()
            lines.append(f"Kitob: «{book.nomi}», muallif {book.muallif}, javonda {free}/{total} nusxa.")
        rq = Q()
        for w in words:
            rq |= Q(fish__icontains=w)
        for reader in scope(Oquvchi.objects.all(), org).filter(rq)[:3]:
            active = Berish.objects.filter(oquvchi=reader, qaytarilgan_sana__isnull=True)
            overdue = active.filter(qaytarish_muddati__lt=date.today()).count()
            lines.append(
                f"O'quvchi: {reader.fish} ({reader.karta_raqami}), qo'lida {active.count()} kitob, "
                f"shundan muddati o'tgan {overdue}."
            )

    overdue_all = scope(Berish.objects.all(), org).filter(
        qaytarilgan_sana__isnull=True, qaytarish_muddati__lt=date.today()
    ).count()
    lines.append(f"Kutubxonada muddati o'tgan berishlar: {overdue_all} ta.")
    return "Tizimdagi haqiqiy ma'lumotlar (faqat shularga tayan):\n" + "\n".join(lines)


class ChatbotThrottle(UserRateThrottle):
    scope = "chatbot"


def _clean_history(raw) -> list[dict]:
    """Klientdan kelgan tarixni Gemini API formatiga ({'role': ..., 'parts': [{'text': ...}]}) keltiradi."""
    if not isinstance(raw, list):
        return []

    cleaned = []
    for item in raw[-MAX_HISTORY:]:
        if not isinstance(item, dict) or item.get("role") not in ("user", "model"):
            continue

        parts = item.get("parts") or []
        if isinstance(parts, str):
            parts = [parts]

        texts = [p.get("text", "") if isinstance(p, dict) else str(p) for p in parts]
        texts = [t[:MAX_MESSAGE_LEN] for t in texts if t.strip()]

        if texts:
            cleaned.append({"role": item["role"], "parts": [{"text": t} for t in texts]})
    return cleaned


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


# --- API Viewlar ---

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

        history = _clean_history(request.data.get("history"))
        kalit = None
        page = request.data.get("page")
        page = page[:100] if isinstance(page, str) else ""
        context = build_context(request, message, page)

        # Tarixsiz (yangi suhbat) bir xil savol — kvotani tejash uchun keshlanadi.
        # Kontekst kutubxonaga xos, shuning uchun u bilan javob keshlanmaydi.
        if not history and not context:
            kalit = "chatbot:" + hashlib.sha256(message.lower().encode()).hexdigest()
            if (kesh := cache.get(kalit)) is not None:
                _chat_saqlash(request.user, message, kesh)
                return Response({
                    "response": kesh,
                    "history": [
                        {"role": "user", "parts": [message]},
                        {"role": "model", "parts": [kesh]},
                    ],
                })

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                system_instruction=CHATBOT_SYSTEM_INSTRUCTION + ("\n\n" + context if context else ""),
            )
            chat = model.start_chat(history=history)
            response = chat.send_message(message)
            text = response.text or ""
        except ResourceExhausted:
            logger.warning("Gemini kvotasi tugagan")
            return Response({"error": "AI limiti tugadi. Keyinroq urinib ko'ring."}, status=429)
        except Exception:
            logger.exception("Gemini so'rovi muvaffaqiyatsiz")
            return Response({"error": "AI hozir javob bera olmadi. Keyinroq urinib ko'ring."}, status=502)

        if kalit:
            cache.set(kalit, text, 3600)

        # To'liq suhbat tarixini frontend formati bo'yicha shakllantirish
        updated_history = [
            {"role": h["role"], "parts": [p["text"] for p in h["parts"]]}
            for h in history
        ]
        updated_history.append({"role": "user", "parts": [message]})
        updated_history.append({"role": "model", "parts": [text]})

        _chat_saqlash(request.user, message, text)
        return Response({"response": text, "history": updated_history})


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
                model_name=GEMINI_MODEL,
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
    """Admin panelning yagona HTML sahifasi (React SPA shell)."""

    template_name = "web/index.html"