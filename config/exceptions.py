"""
Butun API bo'ylab bitta xato formatini ta'minlaydi: {"error": "...", "detail": "..."}.

Ichki servis funksiyalari (masalan berish/services.py) ValidationError'ni allaqachon
{"error": kod, "detail": matn} shaklida ko'taradi — bu holda handler formatga tegmaydi,
faqat DRF/Django darajasidagi standart xatolarni (403, 404, oddiy ValidationError va h.k.)
shu formatga o'tkazadi.

Muhim chegaraviy holat: serializer ichidagi maydon tekshiruvida (masalan
`validate_oquvchi`) `{"error": "oquvchi_bloklangan", ...}` ko'tarilsa, DRF uni
maydon ostida ro'yxatga aylantiradi —
`{"oquvchi": ["{'error': 'oquvchi_bloklangan', 'detail': 'O'quvchi bloklangan'}"]}`.
Oddiy aylantirishda bot `oquvchi_bloklangan` o'rniga `validatsiya_xatosi` olib,
foydalanuvchiga "O'quvchi bloklangan" o'rniga tushunarsiz xabar ko'rsatardi.
`_ichki_biznes_xatosi` shu kodlarni ichkaridan chiqaradi.
"""
from ast import literal_eval

from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler as drf_exception_handler


def biznes_xato(kod: str, detail: str, **qoshimcha) -> ValidationError:
    """Biznes qoidasi xatosini `{"error": kod, "detail": matn}` shaklida qaytaradi.

    Serializer maydon tekshiruvida ham ishlatilishi mumkin — kod shu holda ham
    saqlanib qoladi (pastdagi `_ichki_biznes_xatosi` orqali).
    """
    return ValidationError({"error": kod, "detail": detail, **qoshimcha})


def _ichki_biznes_xatosi(qiymat):
    """`str`, ro'yxat yoki lug'at ichidagi `{'error': ..., 'detail': ...}`
    strukturasi topiladi va asosiy formatga qaytariladi. Topilmasa — None.

    DRF maydon ichidagi ValidationError'ni `{'oquvchi': [{'error': ...}]}` yoki
    `{'oquvchi': ["{'error': ...}"]}` ko'rinishida beradi — ikkala holatni
    ham qayta qaytarishimiz kerak.
    """
    if isinstance(qiymat, dict):
        if "error" in qiymat and "detail" in qiymat:
            natija = {
                "error": _birinchi_qiymat(qiymat["error"]),
                "detail": _birinchi_qiymat(qiymat["detail"]),
            }
            for kalit, ichki_qiymat in qiymat.items():
                if kalit not in ("error", "detail"):
                    natija[kalit] = _birinchi_qiymat(ichki_qiymat)
            return natija
        for ichki in qiymat.values():
            natija = _ichki_biznes_xatosi(ichki)
            if natija:
                return natija
        return None

    if isinstance(qiymat, (list, tuple)):
        for element in qiymat:
            natija = _ichki_biznes_xatosi(element)
            if natija:
                return natija
        return None

    if not isinstance(qiymat, str) or "'error':" not in qiymat:
        return None

    boshlanish = qiymat.find("{'error':")
    if boshlanish == -1:
        return None
    try:
        lugat = literal_eval(qiymat[boshlanish:])
    except (ValueError, SyntaxError):
        return None
    if isinstance(lugat, dict) and "error" in lugat and "detail" in lugat:
        return {kalit: _birinchi_qiymat(q) for kalit, q in lugat.items()}
    return None


def _birinchi_qiymat(qiymat):
    """DRF ba'zi qiymatlarni ro'yxat qilib qaytaradi — birinchisini olamiz."""
    if isinstance(qiymat, (list, tuple)):
        return str(qiymat[0]) if qiymat else ""
    return str(qiymat)


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
        ichkisi = _ichki_biznes_xatosi(data["detail"])
        if ichkisi:
            response.data = ichkisi
            return response
        response.data = {"error": "xato", "detail": str(data["detail"])}
        return response

    if isinstance(data, dict):
        # Serializer maydoni ichidagi biznes xatosi — asosiy kodni saqlab qolamiz.
        for qiymat in data.values():
            ichkisi = _ichki_biznes_xatosi(qiymat)
            if ichkisi:
                response.data = ichkisi
                return response

        birinchi_maydon = next(iter(data))
        xabar = data[birinchi_maydon]
        if isinstance(xabar, list):
            xabar = xabar[0] if xabar else "Noto'g'ri so'rov"
        response.data = {"error": "validatsiya_xatosi", "detail": f"{birinchi_maydon}: {xabar}"}
        return response

    if isinstance(data, list) and data:
        ichkisi = _ichki_biznes_xatosi(data)
        if ichkisi:
            response.data = ichkisi
            return response
        response.data = {"error": "validatsiya_xatosi", "detail": str(data[0])}
        return response

    return response
