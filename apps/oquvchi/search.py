"""Ism-familyalarni qidirishda apostrof/tire farqiga chidamlik.

Telefon klaviaturasida oddiy `'` (U+0027) yoziladi, bazadagi ismlarda esa
ko'pincha tipografik belgilar turadi: `‘` (U+2018), `’` (U+2019), `ʻ`
(U+02BB), `ʼ` (U+02BC). Natijada PWA'dan "Jo'rayeva" deb yozilgan qidiruv
"Jo‘rayeva Nargizaxon"ni topolmaydi, stolda esa belgini nusxalab yozganda
topiladi. Tire uchun ham xuddi shunday (``-`` / ``–`` / ``—``).

Bu filter backend DRF ninng standart SearchFilter o'rniga ishlatiladi:
har bir so'z uchun barcha mumkin bo'lgan belgi variantlari OR bilan
birlashtiriladi, so'zlar esa avvalgidek AND bilan (ikkalasi ham ismda
bo'lishi shart).
"""
import re

from django.db.models import Q
from rest_framework.filters import SearchFilter

# Oddiy apostrofga almashtiriladigan belgilar.
APOSTROFLAR = (
    "\u2018",  # ‘
    "\u2019",  # ’
    "\u02bb",  # ʻ
    "\u02bc",  # ʼ
    "\u0060",  # `
    "\u00b4",  # ´
    "\u201b",  # ‛
)
TIREREZGARLAR = (
    "\u2010",  # ‐
    "\u2011",  # ‑
    "\u2012",  # ‒
    "\u2013",  # –
    "\u2014",  # —
)


APOSTROPHE_CLASS = "[" + "'" + "".join(APOSTROFLAR) + "]"
DASH_CLASS = "[-" + "".join(TIREREZGARLAR) + "]"


# New-alphabet letters typed in several ways: oʻ = o' = õ = ö ..., gʻ = g' = ğ ...
_O_VARIANTS = "oOõÕöÖóÓòÒōŌŏŎ"
_G_VARIANTS = "ğĞǵǴĝĜ"


def _letter(ch: str) -> str:
    """Both cases of one character, built in Python so the DB collation does not matter."""
    variants = {ch, ch.lower(), ch.upper()}
    if len(variants) == 1 or any(len(v) != 1 for v in variants):
        return re.escape(ch)
    return "[" + "".join(re.escape(v) for v in sorted(variants)) + "]"


def search_pattern(term: str) -> str:
    """Regex for `term` that ignores case, apostrophe and dash variants.

    Stored names mix several typographic marks (`ʼ`, `ʻ`, `‘` ...), phone
    keyboards type yet another one or none at all, and some people write the
    new-alphabet letters as `õ` / `ğ`. So: case is matched in both forms
    explicitly (the database may run with the C collation, where `~*` folds
    only ASCII), apostrophes in the term are dropped and allowed after every
    character, `o`/`g` also match `õ`/`ğ`, and any dash matches any dash.
    """
    optional_apostrophe = APOSTROPHE_CLASS + "?"
    parts = []
    for ch in term:
        if ch == "'" or ch in APOSTROFLAR:
            continue
        if ch == "-" or ch in TIREREZGARLAR:
            parts.append(DASH_CLASS)
            continue
        if ch in _O_VARIANTS:
            parts.append("(?:[oO]|[" + _O_VARIANTS[2:] + "])")
        elif ch in "gG" or ch in _G_VARIANTS:
            parts.append("(?:[gG]|[" + _G_VARIANTS + "])")
        else:
            parts.append(_letter(ch))
        parts.append(optional_apostrophe)
    return "".join(parts)


def tolerant_q(fields, text: str) -> Q:
    """Every word of `text` must match one of `fields` (see `search_pattern`)."""
    condition = Q()
    for word in text.split():
        pattern = search_pattern(word)
        if not pattern:
            continue
        any_field = Q()
        for field in fields:
            any_field |= Q(**{f"{field}__regex": pattern})
        condition &= any_field
    return condition


class ChidamliQidiruvFilter(SearchFilter):
    """`?search=` bo'yicha belgi variantlarini ham hisobga oladigan filter."""

    def filter_queryset(self, request, queryset, view):
        maydonlar = self.get_search_fields(view, request) or getattr(view, "search_fields", None)
        sozlar = self.get_search_terms(request)
        if not maydonlar or not sozlar:
            return queryset

        # DRF prefixes ("^", "=", "@", "$") are not used by our views.
        fields = [f.lstrip("^=@$") for f in maydonlar]
        query = queryset.filter(tolerant_q(fields, " ".join(sozlar)))
        # Matching through a to-many relation can repeat rows.
        return query.distinct() if any("__" in f for f in fields) else query


# English name for the project-wide default backend.
TolerantSearchFilter = ChidamliQidiruvFilter
