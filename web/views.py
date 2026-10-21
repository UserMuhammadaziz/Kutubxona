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
            message = data.get("message", "")
            history = data.get("history", [])

            if not message:
                return JsonResponse({"error": "Message is required"}, status=400)

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            chat = model.start_chat(history=history)
            response = chat.send_message(message)

            return JsonResponse(
                {
                    "response": response.text,
                    "history": [
                        {"role": "user", "parts": [message]},
                        {"role": "model", "parts": [response.text]},
                    ],
                }
            )
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
