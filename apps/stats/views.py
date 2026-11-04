from django.db.models import Avg, Count, Q
from django.utils.timezone import now
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from berish.models import Berish
from jarima.models import Jarima
from kitob.models import Kitob
from navbat.models import Navbat
from nusxa.models import Nusxa
from organization.models import Organization
from organization.tenancy import joriy_kutubxonani_aniqla, scope
from oquvchi.models import Oquvchi
from user.permissions import IsLibrarian

from .models import LibraryActivityRating, LibraryRating


def _faollik_hisobla(organization):
    oquvchilar = Oquvchi.objects.filter(organization=organization, faol=True)
    oquvchi_soni = oquvchilar.count()
    oqituvchi_soni = oquvchilar.filter(rol="oqituvchi").count()
    oquvchi_nafaqadagi = oquvchilar.filter(rol="oquvchi").count()
    berishlar = Berish.objects.filter(organization=organization)
    berishlar_soni = berishlar.count()
    qaytarilgan_soni = berishlar.filter(qaytarilgan_sana__isnull=False).count()
    faol_berishlar = berishlar.filter(qaytarilgan_sana__isnull=True).count()
    jarimalar = Jarima.objects.filter(organization=organization, tolandimi=False).count()
    bot_ulangan = hasattr(organization, "telegram_bot") and organization.telegram_bot.holati == "ulangan"

    oquvchi_bali = min(100, oquvchi_soni * 2 + faol_berishlar * 3)
    sinf_bali = 0
    # sinf bo'yicha faollik
    for sinf in oquvchilar.filter(rol="oquvchi").values_list("sinf", flat=True).distinct():
        if sinf:
            s_b = berishlar.filter(oquvchi__sinf=sinf).count()
            sinf_bali += min(20, s_b * 2)
    oqituvchi_bali = min(100, oqituvchi_soni * 5 + berishlar.filter(oquvchi__rol="oqituvchi").count() * 3)
    umumiy_bali = round((oquvchi_bali + min(100, sinf_bali) + oqituvchi_bali - jarimalar * 2 + (10 if bot_ulangan else 0)) / 3, 2)
    if umumiy_bali < 0:
        umumiy_bali = 0

    reyting, _ = LibraryActivityRating.objects.update_or_create(
        organization=organization,
        defaults={
            "oquvchi_bali": oquvchi_bali,
            "sinf_bali": min(100, sinf_bali),
            "oqituvchi_bali": oqituvchi_bali,
            "umumiy_bali": umumiy_bali,
            "oquvchi_soni": oquvchi_soni,
            "faol_oquvchi_soni": berishlar.filter(qaytarilgan_sana__isnull=True).values("oquvchi").distinct().count(),
            "berishlar_soni": berishlar_soni,
            "qaytarilgan_soni": qaytarilgan_soni,
        },
    )
    return reyting


@api_view(["GET"])
@permission_classes([IsLibrarian])
def top_books(request):
    org = joriy_kutubxonani_aniqla(request, required=False)
    raw_limit = request.query_params.get("limit", 10)
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        raise ValidationError({"limit": "Butun son kiritishingiz kerak."})
    if limit < 1 or limit > 100:
        raise ValidationError({"limit": "1 dan 100 gacha son kiritishingiz kerak."})

    berishlar_soni = Count("nusxalar__berish", distinct=True) + Count(
        "berishlar", filter=Q(berishlar__nusxa__isnull=True), distinct=True
    )
    qs = scope(Kitob.objects, org).annotate(berishlar_soni=berishlar_soni).order_by(
        "-berishlar_soni"
    )[:limit]
    data = [
        {"id": k.id, "nomi": k.nomi, "muallif": k.muallif, "berishlar_soni": k.berishlar_soni}
        for k in qs
    ]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsLibrarian])
def dashboard(request):
    org = joriy_kutubxonani_aniqla(request, required=False)
    jami_nusxalar = scope(Nusxa.objects, org).count()
    mavjud_nusxalar = scope(Nusxa.objects, org).filter(holati="mavjud").count()
    berilgan_nusxalar = scope(Nusxa.objects, org).filter(holati="berilgan").count()
    muddati_otgan = scope(Berish.objects, org).filter(
        qaytarilgan_sana__isnull=True, qaytarish_muddati__lt=now().date()
    ).count()
    faol_navbatlar = scope(Navbat.objects, org).filter(
        holati__in=["kutmoqda", "taklif_qilindi"]
    ).count()
    tolanmagan_jarima = scope(Jarima.objects, org).filter(tolandimi=False)
    umumiy_qarz = sum(j.summa for j in tolanmagan_jarima)
    
    oquvchi_soni = Oquvchi.objects.filter(organization=org, rol='oquvchi', faol=True).count()
    oqituvchi_soni = Oquvchi.objects.filter(organization=org, rol='oqituvchi', faol=True).count()

    return Response(
        {
            "jami_kitoblar": scope(Kitob.objects, org).count(),
            "jami_nusxalar": jami_nusxalar,
            "mavjud_nusxalar": mavjud_nusxalar,
            "berilgan_nusxalar": berilgan_nusxalar,
            "muddati_otgan_berishlar": muddati_otgan,
            "faol_navbatlar": faol_navbatlar,
            "tolanmagan_jarimalar_soni": tolanmagan_jarima.count(),
            "umumiy_qarz": umumiy_qarz,
            "oquvchi_soni": oquvchi_soni,
            "oqituvchi_soni": oqituvchi_soni,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def library_ratings(request):
    org = joriy_kutubxonani_aniqla(request, required=True)
    reyting = (
        LibraryRating.objects.filter(organization=org)
        .aggregate(ortacha=Avg("baho"), soni=Count("id"))
    )
    m = LibraryRating.objects.filter(organization=org).values("baho").annotate(c=Count("id"))
    taqsimot = {i: 0 for i in range(1, 6)}
    for r in m:
        taqsimot[r["baho"]] = r["c"]
    so_nggi = (
        LibraryRating.objects.filter(organization=org)
        .select_related("oquvchi")
        .order_by("-yangilangan")[:10]
    )
    return Response(
        {
            "organization": {"id": org.id, "nomi": org.nomi},
            "ortacha": reyting["ortacha"],
            "soni": reyting["soni"] or 0,
            "taqsimot": taqsimot,
            "sharhlar": [
                {
                    "baho": x.baho,
                    "izoh": x.izoh,
                    "oquvchi": x.oquvchi.fish,
                    "yangilangan": x.yangilangan,
                }
                for x in so_nggi
            ],
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def library_overall(request):
    org = joriy_kutubxonani_aniqla(request, required=False)
    if org is None and not request.user.is_superuser:
        raise ValidationError({"organization": "Kutubxonani tanlang."})
    qs = Organization.objects.filter(faol=True)
    if org and not request.user.is_superuser:
        qs = qs.filter(pk=org.pk)
    natija = []
    for kutubxona in qs.annotate(
        ortacha=Avg("reytinglar__baho"), soni=Count("reytinglar")
    ).order_by("-ortacha", "-soni"):
        natija.append(
            {
                "id": kutubxona.id,
                "nomi": kutubxona.nomi,
                "slug": kutubxona.slug,
                "ortacha": kutubxona.ortacha,
                "soni": kutubxona.soni or 0,
            }
        )
    if request.user.is_superuser and org is None:
        natija = sorted(natija, key=lambda x: (x["ortacha"] or 0, x["soni"]), reverse=True)
    return Response(natija)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def faollik_reytingi(request):
    org = joriy_kutubxonani_aniqla(request, required=True)
    reyting = _faollik_hisobla(org)
    # sinf va o'qituvchilar bo'yicha qisqacha
    sinflar = []
    for sinf in (
        Oquvchi.objects.filter(organization=org, rol="oquvchi", faol=True)
        .values("sinf")
        .annotate(soni=Count("id"))
        .order_by("sinf")
    ):
        if sinf["sinf"]:
            b = Berish.objects.filter(organization=org, oquvchi__sinf=sinf["sinf"]).count()
            sinflar.append({"sinf": sinf["sinf"], "oquvchilar": sinf["soni"], "berishlar": b})
    oqituvchilar = []
    for t in (
        Oquvchi.objects.filter(organization=org, rol="oqituvchi", faol=True)
        .values("fish", "kasb")
        .annotate(berishlar=Count("berish"))
    ):
        oqituvchilar.append({"fish": t["fish"], "kasb": t["kasb"], "berishlar": t["berishlar"]})
    oqituvchilar.sort(key=lambda x: x["berishlar"], reverse=True)
    return Response(
        {
            "organization": {"id": org.id, "nomi": org.nomi},
            "umumiy_bali": reyting.umumiy_bali,
            "oquvchi_bali": reyting.oquvchi_bali,
            "sinf_bali": reyting.sinf_bali,
            "oqituvchi_bali": reyting.oqituvchi_bali,
            "faol_oquvchi_soni": reyting.faol_oquvchi_soni,
            "oquvchi_soni": reyting.oquvchi_soni,
            "berishlar_soni": reyting.berishlar_soni,
            "qaytarilgan_soni": reyting.qaytarilgan_soni,
            "sinflar": sinflar,
            "oqituvchilar": oqituvchilar[:20],
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def umummiy_bellashuv(request):
    natija = []
    for org in Organization.objects.filter(faol=True):
        reyting = _faollik_hisobla(org)
        natija.append(
            {
                "id": org.id,
                "nomi": org.nomi,
                "umumiy_bali": reyting.umumiy_bali,
                "oquvchi_bali": reyting.oquvchi_bali,
                "sinf_bali": reyting.sinf_bali,
                "oqituvchi_bali": reyting.oqituvchi_bali,
                "berishlar_soni": reyting.berishlar_soni,
                "oquvchi_soni": reyting.oquvchi_soni,
            }
        )
    natija.sort(key=lambda x: x["umumiy_bali"], reverse=True)
    for i, x in enumerate(natija, 1):
        x["o_rin"] = i
    return Response(natija)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rate_library(request):
    org = joriy_kutubxonani_aniqla(request, required=True)
    baho = request.data.get("baho")
    try:
        baho = int(baho)
    except (TypeError, ValueError):
        raise ValidationError({"baho": "1-5 orasida baho kiriting."})
    if baho < 1 or baho > 5:
        raise ValidationError({"baho": "1-5 orasida baho kiriting."})
    oquvchi = Oquvchi.objects.filter(organization=org, telegram_id__isnull=False).first()
    if not oquvchi:
        for o in Oquvchi.objects.filter(organization=org, faol=True):
            if o.telegram_id:
                oquvchi = o
                break
    if not oquvchi:
        raise ValidationError(
            {"detail": "Reyting berish uchun avval Telegram bot orqali ro'yxatdan o'ting."}
        )
    reyting, _ = LibraryRating.objects.update_or_create(
        organization=org,
        oquvchi=oquvchi,
        defaults={"baho": baho, "izoh": (request.data.get("izoh") or "")[:255]},
    )
    _faollik_hisobla(org)
    return Response({"ok": True, "baho": reyting.baho})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_ratings(request):
    org = joriy_kutubxonani_aniqla(request, required=False)
    qs = LibraryRating.objects.filter(oquvchi__telegram_id__isnull=False)
    if org:
        qs = qs.filter(organization=org)
    return Response(
        [
            {
                "organization_id": r.organization_id,
                "organization_nomi": r.organization.nomi,
                "baho": r.baho,
                "izoh": r.izoh,
                "yangilangan": r.yangilangan,
            }
            for r in qs[:20]
        ]
    )


