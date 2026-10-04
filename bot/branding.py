"""Bot xabarlari uchun zamonaviy «logo» va yagona ko'rinish uslublari.

Avval xabarlar bo'lib-bo'lib turgan emoji (🔒 📖 ✅ ⏳ ❌ 🚪) ishlatardi —
ular har bir joyda boshqacha ko'rinar va xabarni «bolalarcha» qilib
ko'rsatardi. Endi bitta markaziy uslub bor:

* :func:`logo` — xabarning tepasidagi kichik «logo» sarlavhasi;
* :func:`sarlavha` — bo'lim nomi;
* :func:`holat_nomi` — band/berish holatining toza yozuvi;
* :func:`chiziq` — yupiq ajratgich.

Barcha matnlar HTML formatida (`parse_mode="HTML"`), shuning uchun
`<b>` teglari ishlatiladi. Telegram `━` va `◈` belgilarni to'g'ri
ko'rsatadi.
"""

# Markaziy logo. `◈` — oddiy, zamonaviy ko'rinadigan belgi; emoji emas.
LOGO_IKON = "◈"
LOGO_NOM = "KUTUBXONA"

# Ajratgich uzunligi — Telegram matn maydoniga sig'adi (≈34 belgi).
_CHIZIQ = "━━━━━━━━━━━━━━━━━━━━━━"

# Holat -> (belgi, matn). Belgilar ataylab minimallashtirilgan: har bir
# holat uchun bittagina, ma'nosi aniq bo'lgan belgi.
_BAND_HOLATLARI = {
    "kutmoqda": ("◷", "Kutubxonachi tasdiqlashini kutilmoqda"),
    "tasdiqlandi": ("✔", "Tasdiqlandi — kitob sizga berildi"),
    "rad_etildi": ("✖", "Rad etildi"),
    "bekor_qilindi": ("↩", "Siz bekor qilgansiz"),
}

_BERISH_HOLATLARI = {
    "faol": ("◷", "Sizda"),
    "qaytarilgan": ("✔", "Qaytarilgan"),
    "kechiktirildi": ("!", "Muddati o'tdi"),
}


def chiziq() -> str:
    """Yupiq ajratgich."""
    return _CHIZIQ


def logo(nom: str = LOGO_NOM, sarlavha: str | None = None) -> str:
    """Xabarning tepasidagi «logo» bloki.

    Args:
        nom: markaziy nom (odatda ``KUTUBXONA``).
        sarlavha: ixtiyoriy bo'lim nomi — berilsa, chiziq ostida chiqadi.

    Returns:
        ``◈ KUTUBXONA ◈`` + ajratgich (+ bo'lim nomi) matni.
    """
    qator = f"<b>{LOGO_IKON} {nom} {LOGO_IKON}</b>"
    blok = f"{qator}\n{_CHIZIQ}"
    if sarlavha:
        blok += f"\n<b>{sarlavha}</b>"
    return blok


def sarlavha(matn: str) -> str:
    """Bo'lim sarlavhasi (chiziqsiz, qisqa)."""
    return f"<b>{matn}</b>"


def holat_nomi(holati: str, *, tur: str = "band") -> str:
    """Band yoki berish holatini belgi + matn ko'rinishida qaytaradi.

    Noma'lum holatlar uchun `None` qaytaradi — caller o'z matnini qo'yadi.
    """
    if tur == "band":
        jadval = _BAND_HOLATLARI
    elif tur == "berish":
        jadval = _BERISH_HOLATLARI
    else:
        raise ValueError(f"tur noma'lum: {tur!r}")
    topilgan = jadval.get(holati)
    if topilgan is None:
        return None
    belgi, matn = topilgan
    return f"{belgi} {matn}"


def band_holati(holati: str) -> str:
    """Band holati uchun qulay qisqa nusxa (``holat_nomi(..., tur='band')``)."""
    return holat_nomi(holati, tur="band") or f"• {holati}"