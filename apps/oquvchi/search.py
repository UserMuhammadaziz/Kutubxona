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


def qidiruv_variantlari(soz: str) -> list[str]:
    """Berilgan so'zning barcha apostrof/tire ko'rinishlari."""
    variantlar = {soz}
    for belgi in APOSTROFLAR:
        for manba, maqsad in (("'", belgi), (belgi, "'")):
            if manba in soz:
                variantlar.add(soz.replace(manba, maqsad))
    for belgi in TIREREZGARLAR:
        for manba, maqsad in (("-", belgi), (belgi, "-")):
            if manba in soz:
                variantlar.add(soz.replace(manba, maqsad))
    return list(variantlar)


class ChidamliQidiruvFilter(SearchFilter):
    """`?search=` bo'yicha belgi variantlarini ham hisobga oladigan filter."""

    def filter_queryset(self, request, queryset, view):
        maydonlar = self.get_search_fields(view, request) or getattr(view, "search_fields", None)
        sozlar = self.get_search_terms(request)
        if not maydonlar or not sozlar:
            return queryset

        shart = Q()
        for qism in sozlar:
            variant_sharti = Q()
            for variant in qidiruv_variantlari(qism):
                for maydon in maydonlar:
                    variant_sharti |= Q(**{f"{maydon}__icontains": variant})
            shart &= variant_sharti
        return queryset.filter(shart)
