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


def search_pattern(term: str) -> str:
    """Case-insensitive regex for `term` where every apostrophe or dash matches any variant.

    Stored names mix several typographic marks (`ʼ`, `ʻ`, `‘` ...) and phone
    keyboards type yet another one, so a plain substring search misses them.
    Everything else in the term is matched literally.
    """
    parts = []
    for ch in term:
        if ch == "'" or ch in APOSTROFLAR:
            parts.append(APOSTROPHE_CLASS)
        elif ch == "-" or ch in TIREREZGARLAR:
            parts.append(DASH_CLASS)
        else:
            parts.append(re.escape(ch))
    return "".join(parts)


class ChidamliQidiruvFilter(SearchFilter):
    """`?search=` bo'yicha belgi variantlarini ham hisobga oladigan filter."""

    def filter_queryset(self, request, queryset, view):
        maydonlar = self.get_search_fields(view, request) or getattr(view, "search_fields", None)
        sozlar = self.get_search_terms(request)
        if not maydonlar or not sozlar:
            return queryset

        shart = Q()
        for qism in sozlar:
            pattern = search_pattern(qism)
            variant_sharti = Q()
            for maydon in maydonlar:
                variant_sharti |= Q(**{f"{maydon}__iregex": pattern})
            shart &= variant_sharti
        return queryset.filter(shart)
