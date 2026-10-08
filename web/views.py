from pathlib import Path

from django.http import FileResponse, Http404
from django.views.generic import TemplateView

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
