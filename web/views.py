import json
import os
from pathlib import Path

from django.http import FileResponse, Http404, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

try:
    import google.generativeai as genai
except ImportError:
    genai = None

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



# Model nomi .env orqali almashtiriladi (masalan GEMINI_MODEL=gemini-2.5-flash).
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

SYSTEM_INSTRUCTION = (
    "Siz — «Kutubxona» kutubxonaviy boshqaruv tizimining yordamchisiz. "
    "Faqat o'zbek tilida, qisqa va aniq javob bering. Kitob fondi, "
    "kitob berish-qaytarish, o'quvchilar, navbat, jarima va bandlar "
    "bo'yicha savollarga yordam bering. Ma'lumotni o'zingiz to'qimang."
)


def _clean_history(raw):
    """Frontend kelgan historyni Gemini API formatiga keltiradi.

    Frontend sodda formatda saqlaydi: {"role": "user"|"model", "parts": ["..."]}.
    Gemini SDK esa `parts` ro'yxatida `{"text": "..."}` obyektlarini talab qiladi.
    Noto'g'ri kirishlar (begona role, bo'sh matn) tashlab yuboriladi.
    """
    cleaned = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        if role not in ("user", "model"):
            continue
        parts = item.get("parts") or []
        if isinstance(parts, str):
            parts = [parts]
        texts = [p.get("text", "") if isinstance(p, dict) else str(p) for p in parts]
        texts = [t for t in texts if t]
        if not texts:
            continue
        cleaned.append({"role": role, "parts": [{"text": t} for t in texts]})
    return cleaned


@method_decorator(csrf_exempt, name="dispatch")
class ChatbotView(View):
    """Gemini API proxy endpoint for chatbot."""

    def post(self, request):
        if genai is None:
            return JsonResponse(
                {"error": "google-generativeai package not installed"},
                status=500,
            )

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return JsonResponse(
                {"error": "GEMINI_API_KEY environment variable not set"},
                status=500,
            )

        try:
            data = json.loads(request.body)
            message = (data.get("message") or "").strip()
            history = _clean_history(data.get("history"))

            if not message:
                return JsonResponse({"error": "Message is required"}, status=400)

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                system_instruction=SYSTEM_INSTRUCTION,
            )

            chat = model.start_chat(history=history)
            response = chat.send_message(message)
            text = response.text or ""

            # Frontendga sodda formatda qaytaramiz (parts: ["..."]) va to'liq
            # suhbat tarixini saqlaymiz — oldingi versiya faqat oxirgi
            # almashinuvni qaytarib, ko'p qadamli kontekstni yo'qotardi.
            new_history = list(history)
            new_history.append({"role": "user", "parts": [{"text": message}]})
            new_history.append({"role": "model", "parts": [{"text": text}]})
            simple_history = [
                {
                    "role": h["role"],
                    "parts": [p["text"] for p in h["parts"]],
                }
                for h in new_history
            ]

            return JsonResponse({"response": text, "history": simple_history})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


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
