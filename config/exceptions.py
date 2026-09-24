"""
Butun API bo'ylab bitta xato formatini ta'minlaydi: {"error": "...", "detail": "..."}.

Ichki servis funksiyalari (masalan berish/services.py) ValidationError'ni allaqachon
{"error": kod, "detail": matn} shaklida ko'taradi — bu holda handler formatga tegmaydi,
faqat DRF/Django darajasidagi standart xatolarni (403, 404, oddiy ValidationError va h.k.)
shu formatga o'tkazadi.
"""
from rest_framework.views import exception_handler as drf_exception_handler


def xato_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return response

    data = response.data

    # Servis funksiyalaridan kelgan {"error": ..., "detail": ...} formatini o'zgartirmaymiz
    if isinstance(data, dict) and "error" in data and "detail" in data:
        # Serializer ichidagi dict-form ValidationError'da qiymatlar ro'yxat bo'lib kelishi
        # mumkin (DRF uni field->xato deb talqin qiladi) — ularni bitta qatorga keltiramiz.
        for kalit in ("error", "detail"):
            qiymat = data[kalit]
            if isinstance(qiymat, list):
                data[kalit] = qiymat[0] if qiymat else str(qiymat)
        return response

    # DRF standart formatlarini ({"detail": "..."} yoki {"field": [...]})  bitta formatga keltiramiz
    if isinstance(data, dict) and "detail" in data and len(data) == 1:
        response.data = {"error": "xato", "detail": str(data["detail"])}
        return response

    if isinstance(data, dict):
        birinchi_maydon = next(iter(data))
        xabar = data[birinchi_maydon]
        if isinstance(xabar, list):
            xabar = xabar[0] if xabar else "Noto'g'ri so'rov"
        response.data = {"error": "validatsiya_xatosi", "detail": f"{birinchi_maydon}: {xabar}"}
        return response

    if isinstance(data, list) and data:
        response.data = {"error": "validatsiya_xatosi", "detail": str(data[0])}
        return response

    return response
