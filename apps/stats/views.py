from django.utils.timezone import now
from django.db.models import Count, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from berish.models import Berish
from jarima.models import Jarima
from kitob.models import Kitob
from navbat.models import Navbat
from nusxa.models import Nusxa
from user.permissions import IsLibrarian


@api_view(["GET"])
@permission_classes([IsLibrarian])
def top_books(request):
    """GET /api/stats/top-books/?limit=10 — eng ko'p berilgan kitoblar reytingi."""
    # `int()` xatosi 500 qaytarardi (masalan `?limit=abc`). Noto'g'ri
    # yoki manfiy qiymat uchun 400 — foydalanuvchi nima qilishini biladi.
    raw_limit = request.query_params.get("limit", 10)
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        raise ValidationError({"limit": "Butun son kiritishingiz kerak."})
    if limit < 1 or limit > 100:
        raise ValidationError({"limit": "1 dan 100 gacha son kiritishingiz kerak."})

    # Berishlar ikki turda bo'ladi: nusxa orqali (nusxalar__berish) va
    # nusxasi yo'q kitobni «asli» holda berish (kitob_id to'g'ridan-to'g'ri).
    # Faqat birinchisini hisoblashda asli berilganlar reytingda yo'q edi.
    berishlar_soni = Count("nusxalar__berish", distinct=True) + Count(
        "berishlar", filter=Q(berishlar__nusxa__isnull=True), distinct=True
    )
    qs = (
        Kitob.objects.annotate(berishlar_soni=berishlar_soni)
        .order_by("-berishlar_soni")[:limit]
    )
    data = [
        {"id": k.id, "nomi": k.nomi, "muallif": k.muallif, "berishlar_soni": k.berishlar_soni}
        for k in qs
    ]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsLibrarian])
def dashboard(request):
    """GET /api/stats/dashboard/ — umumiy raqamlar: fond, berilgan, muddati o'tgan, navbat, qarz."""
    jami_nusxalar = Nusxa.objects.count()
    mavjud_nusxalar = Nusxa.objects.filter(holati="mavjud").count()
    berilgan_nusxalar = Nusxa.objects.filter(holati="berilgan").count()
    muddati_otgan = Berish.objects.filter(
        qaytarilgan_sana__isnull=True, qaytarish_muddati__lt=now().date()
    ).count()
    faol_navbatlar = Navbat.objects.filter(holati__in=["kutmoqda", "taklif_qilindi"]).count()
    tolanmagan_jarima = Jarima.objects.filter(tolandimi=False)
    umumiy_qarz = sum(j.summa for j in tolanmagan_jarima)

    return Response(
        {
            "jami_kitoblar": Kitob.objects.count(),
            "jami_nusxalar": jami_nusxalar,
            "mavjud_nusxalar": mavjud_nusxalar,
            "berilgan_nusxalar": berilgan_nusxalar,
            "muddati_otgan_berishlar": muddati_otgan,
            "faol_navbatlar": faol_navbatlar,
            "tolanmagan_jarimalar_soni": tolanmagan_jarima.count(),
            "umumiy_qarz": umumiy_qarz,
        }
    )
