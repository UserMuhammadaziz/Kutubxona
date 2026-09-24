from django.views.generic import TemplateView


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
