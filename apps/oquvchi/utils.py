"""Sinf nomlarini yagona ko'rinishga keltirish.

Turli manbalardan (bot, kutubxonachi formasi, eski ma'lumotlar) kelgan
`5-B`, `5-B sinf`, `5b`, `5 - B`, `5-В` kabi qiymatlar bitta sinf hisoblanishi
kerak. Reyting va xabar yuborish shu kanonik kalit bo'yicha guruhlanadi.
"""
import re
import unicodedata

# Oxiridagi "sinf"/"sinfi" qo'shimchasi (ixtiyoriy chiziqcha bilan).
_SINF_OXIRI = re.compile(r"\s*-?\s*(?:sinf|sinfi|class)\s*$", re.IGNORECASE)
# 5-A, 10-, 11-V, 5b, 5 - B ko'rinishlari.
_SINF_SHABLON = re.compile(r"^(\d{1,2})\s*-?\s*([A-Za-z]?)$")
# Eski bazada uchraydigan kirill litralarini lotinga o'tkazish.
_KIRILL = str.maketrans(
    {"А": "A", "а": "A", "В": "B", "в": "B", "Б": "B", "б": "B", "С": "C", "с": "C"}
)


def sinf_normal(qiymat) -> str:
    """Sinfning yagona ko'rinishi: ``5-B``. Bo'sh qiymat -> ``''``."""
    matn = unicodedata.normalize("NFKC", "" if qiymat is None else str(qiymat)).strip()
    matn = _SINF_OXIRI.sub("", matn).strip()
    if not matn:
        return ""
    mos = _SINF_SHABLON.fullmatch(matn)
    if not mos:
        # Noma'lum format bo'lsa ham baribir bitta ko'rinishga keltiramiz.
        return matn.upper().translate(_KIRILL)
    raqam, harf = mos.groups()
    harf = harf.upper().translate(_KIRILL)
    return f"{int(raqam)}-{harf}" if harf else f"{int(raqam)}-"


def sinf_kaliti(sinf: str):
    """Tabiiy tartib uchun kalit: 5-A < 5-B < 10-A."""
    mos = re.match(r"^(\d+)", sinf or "")
    return (int(mos.group(1)) if mos else 999, sinf or "")
