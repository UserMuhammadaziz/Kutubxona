from collections import defaultdict

from django.core.cache import cache
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
from organization.dashboard import available_widgets, dashboard_widgets
from organization.models import Organization
from organization.permissions import IsPlatformAdmin
from organization.tenancy import joriy_kutubxonani_aniqla, scope
from oquvchi.models import Ariza, Oquvchi
from oquvchi.utils import sinf_kaliti, sinf_normal
from config.cache import stats_versiyasi
from user.permissions import IsLibrarian

from .models import LibraryActivityRating, LibraryRating

STATS_TTL = 60  # soniya; yozuv o'zgarsa signal versiyani oshirib, keshni darrov eskirtiradi


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
    # Sinf bo'yicha faollik. Bir sinf turli yozilishlarda ("5-B", "5-B sinf",
    # "5b") kelsa ham bitta sinf hisoblanishi — ikki barobar hisoblanishning
    # oldini oladi.
    sinf_variantlari = defaultdict(list)
    for xom_sinf in oquvchilar.filter(rol="oquvchi").values_list("sinf", flat=True):
        if xom_sinf:
            sinf_variantlari[sinf_normal(xom_sinf)].append(xom_sinf)
    for variantlar in sinf_variantlari.values():
        s_b = berishlar.filter(oquvchi__sinf__in=variantlar).count()
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

    kalit = f"stats:top:{stats_versiyasi()}:{org.pk if org else 0}:{limit}"
    if (kesh := cache.get(kalit)) is not None:
        return Response(kesh)

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
    cache.set(kalit, data, STATS_TTL)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsLibrarian])
def recent_activity(request):
    """Kutubxona so'nggi harakatlari (kim qilganligi bilan).

    Berish va qaytarish voqealari `bergan_xodim` / `olgan_xodim` orqali
    amalga oshirgan xodimni ko'rsatadi.
    """
    org = joriy_kutubxonani_aniqla(request, required=False)
    raw_limit = request.query_params.get("limit", 8)
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        raise ValidationError({"limit": "Butun son kiritishingiz kerak."})
    limit = max(1, min(limit, 50))

    berishlar = scope(Berish.objects, org).select_related(
        "kitob", "oquvchi", "bergan_xodim", "olgan_xodim"
    )

    harakatlar = []
    for b in berishlar:
        beruvchi = b.bergan_xodim.full_name if b.bergan_xodim else "Kutubxonachi"
        harakatlar.append(
            {
                "id": f"b{b.pk}",
                "turi": "berish",
                "sarlavha": "Kitob berildi",
                "tavsif": f"«{b.kitob.nomi}» · {b.oquvchi.fish}",
                "xodim": beruvchi,
                "vaqt": b.berilgan_sana,
            }
        )
        if b.qaytarilgan_sana:
            oluvchi = b.olgan_xodim.full_name if b.olgan_xodim else "Kutubxonachi"
            harakatlar.append(
                {
                    "id": f"q{b.pk}",
                    "turi": "qaytarish",
                    "sarlavha": "Kitob qaytarildi",
                    "tavsif": f"«{b.kitob.nomi}» · {b.oquvchi.fish}",
                    "xodim": oluvchi,
                    "vaqt": b.qaytarilgan_sana,
                }
            )

    harakatlar.sort(key=lambda x: (x["vaqt"], x["id"]), reverse=True)
    return Response(harakatlar[:limit])


@api_view(["GET"])
@permission_classes([IsLibrarian])
def dashboard(request):
    org = joriy_kutubxonani_aniqla(request, required=False)
    kalit = f"stats:dashboard:{stats_versiyasi()}:{org.pk if org else 0}:{now().date()}"
    if (kesh := cache.get(kalit)) is not None:
        return Response(_with_widgets(kesh, org))
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

    data = {
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
        "members_count": Oquvchi.objects.filter(organization=org, faol=True).count(),
        "pending_applications": Ariza.objects.filter(organization=org, holati="kutmoqda").count(),
        "approved_applications": Ariza.objects.filter(organization=org, holati="tasdiqlandi").count(),
        "readers_by_class": _readers_by_class(org),
    }
    cache.set(kalit, data, STATS_TTL)
    return Response(_with_widgets(data, org))


def _readers_by_class(org):
    """Active students per class; spellings like `7a`, `7-A sinf` count as one class."""
    counts = defaultdict(int)
    rows = Oquvchi.objects.filter(organization=org, rol="oquvchi", faol=True).values_list("sinf", flat=True)
    for raw in rows:
        counts[sinf_normal(raw) or ""] += 1
    return [
        {"class_name": name, "count": counts[name]}
        for name in sorted(counts, key=lambda n: sinf_kaliti(n) if n else (1000, ""))
    ]


def _with_widgets(data, org):
    # Not cached with the numbers: a settings change must show up at once.
    return {**data, "widgets": dashboard_widgets(org) if org else available_widgets(None)}


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


def _faol_kitobxonlar(organization, rol):
    """Hozirda kitob o'qiyotgan a'zolar reytingi (ko'p kitob olgan birinchi).

    `faol_berishlar` — qaytarilmagan berishlar soni, `jami_berishlar` —
    umumiy berishlar soni. Ball kutubxonaning `limit_kitob`iga nisbatan
    0..100 orasida hisoblanadi.
    """
    qator = (
        Oquvchi.objects.filter(
            organization=organization, faol=True, rol=rol
        )
        .annotate(
            faol_berishlar=Count(
                "berish",
                filter=Q(
                    berish__organization=organization,
                    berish__qaytarilgan_sana__isnull=True,
                ),
            ),
            jami_berishlar=Count(
                "berish", filter=Q(berish__organization=organization)
            ),
        )
        .filter(faol_berishlar__gt=0)
    )

    cheklov = max(organization.limit_kitob, 1)
    natija = []
    for azo in qator:
        natija.append(
            {
                "id": azo.pk,
                "fish": azo.fish,
                "sinf": sinf_normal(azo.sinf) if rol == "oquvchi" else "",
                "kasb": azo.kasb if rol == "oqituvchi" else "",
                "faol_berishlar": azo.faol_berishlar,
                "jami_berishlar": azo.jami_berishlar,
                "ball": round(min(100, azo.faol_berishlar / cheklov * 100), 1),
            }
        )
    natija.sort(
        key=lambda x: (x["faol_berishlar"], x["jami_berishlar"]), reverse=True
    )
    for orin, row in enumerate(natija, 1):
        row["o_rin"] = orin
    return natija


def _faol_sinflar(organization):
    """Sinflar reytingi: turli yozilishlar bitta sinfga birlashtiriladi.

    O'rin sinfdagi o'quvchilarning kitob o'qish faolligiga bog'liq:
    hozirda qaytarilmagan kitoblari bor o'quvchilar ulushi asosiy ball hisoblanadi.
    Qaytarilgan berishlar ham kichik ulush bilan hisobga olinadi (faollik izi).
    """
    guruh = defaultdict(list)
    qator = (
        Oquvchi.objects.filter(organization=organization, rol="oquvchi", faol=True)
        .exclude(sinf="")
        .values_list("id", "sinf")
    )
    for oquvchi_id, xom_sinf in qator:
        kalit = sinf_normal(xom_sinf)
        if kalit:
            guruh[kalit].append(oquvchi_id)

    id_to_sinf = {pk: kalit for kalit, ids in guruh.items() for pk in ids}
    if not id_to_sinf:
        return []

    stat = {
        kalit: {"jami": 0, "faol": 0, "qaytarilgan": 0, "faol_oc": set()}
        for kalit in guruh
    }
    berishlar = Berish.objects.filter(
        organization=organization, oquvchi_id__in=list(id_to_sinf)
    ).values_list("oquvchi_id", "qaytarilgan_sana")
    for oquvchi_id, qaytarilgan_sana in berishlar:
        s = stat[id_to_sinf[oquvchi_id]]
        s["jami"] += 1
        if qaytarilgan_sana is None:
            s["faol"] += 1
            s["faol_oc"].add(oquvchi_id)
        else:
            s["qaytarilgan"] += 1

    natija = []
    for kalit, ids in guruh.items():
        s = stat[kalit]
        n = max(len(ids), 1)
        ulush_oquvchi = len(s["faol_oc"]) / n
        ulush_kitob = min(1.0, s["faol"] / n)
        ulush_qaytarilgan = min(1.0, s["qaytarilgan"] / n)
        natija.append(
            {
                "sinf": kalit,
                "oquvchilar": len(ids),
                "berishlar": s["jami"],
                "faol_berishlar": s["faol"],
                "faol_oquvchilar_soni": len(s["faol_oc"]),
                "qaytarilganlar": s["qaytarilgan"],
                # O'qish faolligi ustun turadi: 0.6 o'quvchilar ulushi,
                # 0.3 kitoblar ulushi, 0.1 qaytarilganlar ulushi.
                "ball": round(
                    min(
                        100,
                        100
                        * (
                            0.6 * ulush_oquvchi
                            + 0.3 * ulush_kitob
                            + 0.1 * ulush_qaytarilgan
                        ),
                    ),
                    1,
                ),
            }
        )
    natija.sort(
        key=lambda x: (
            -x["ball"],
            -x["faol_berishlar"],
            -x["faol_oquvchilar_soni"],
            -x["berishlar"],
            sinf_kaliti(x["sinf"]),
        )
    )
    for orin, row in enumerate(natija, 1):
        row["o_rin"] = orin
    return natija


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def faollik_reytingi(request):
    org = joriy_kutubxonani_aniqla(request, required=True)
    reyting = _faollik_hisobla(org)
    sinflar = _faol_sinflar(org)

    # O'qituvchilar reytingi: berishlar va ularning qaytarilishlari bo'yicha.
    oqituvchilar = []
    oqituvchi_qator = Oquvchi.objects.filter(
        organization=org, rol="oqituvchi", faol=True
    ).annotate(
        berishlar=Count("berish"),
        qaytarilganlar=Count("berish", filter=Q(berish__qaytarilgan_sana__isnull=False)),
    )
    for t in oqituvchi_qator:
        ball = round(min(100, t.berishlar * 10 + t.qaytarilganlar * 2), 1)
        oqituvchilar.append(
            {
                "id": t.pk,
                "fish": t.fish,
                "kasb": t.kasb,
                "berishlar": t.berishlar,
                "qaytarilganlar": t.qaytarilganlar,
                "ball": ball,
            }
        )
    oqituvchilar.sort(key=lambda x: (x["ball"], x["berishlar"]), reverse=True)
    for orin, row in enumerate(oqituvchilar, 1):
        row["o_rin"] = orin

    # Hozirda kitob o'qiyotgan (qaytarilmagan berishlari bor) faol a'zolar.
    # Ball kutubxonaning bir o'quvchiga bergan kitoblar limitiga nisbatan
    # hisoblanadi: limitga to'la olgan = 100 ball.
    faol_oquvchilar = _faol_kitobxonlar(org, "oquvchi")
    faol_oqituvchilar = _faol_kitobxonlar(org, "oqituvchi")

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
            "oqituvchilar": oqituvchilar,
            "faol_oquvchilar": faol_oquvchilar,
            "faol_oqituvchilar": faol_oqituvchilar,
        }
    )


@api_view(["GET"])
@permission_classes([IsPlatformAdmin])
def umummiy_bellashuv(request):
    """Compares every library, so only the platform administrator may see it."""
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
    # Fail-closed: tenant aniqlanmasa boshqa kutubxonalarning reytinglarini
    # qaytarmaymiz.
    org = joriy_kutubxonani_aniqla(request, required=True)
    qs = LibraryRating.objects.filter(
        organization=org, oquvchi__telegram_id__isnull=False
    ).select_related("organization")
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


