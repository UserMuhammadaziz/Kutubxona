"""Statistikai va reyting himoyalari uchun Celery tasklari."""

from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q, Avg

from organization.models import Organization, LibraryRating
from kitob.models import Kitob
from nusxa.models import Nusxa
from berish.models import Berish
from oquvchi.models import Oquvchi


def library_ratingni_yangilash(organization_id=None):
    """Kitob, nusxa, berish va o'quvchi ma'lumolar asosida
    tashkilot reytingini haftalik yangilaydi."""
    
    if organization_id:
        organizations = Organization.objects.filter(pk=organization_id)
    else:
        organizations = Organization.objects.filter(status="active")
    
    for org in organizations:
        _organization_rating_yangilash(org)


def _organization_rating_yangilash(organization):
    """Bitta tashkilot uchun reytingni hisoblash."""
    
    # 1. Asosiy reyting ma'lumotlari (o'quvchilarning baholari)
    baholar = LibraryRating.objects.filter(
        organization=organization
    ).values_list("baho", flat=True)
    
    ortacha_bahol = float(baholar.aggregate(avg=Avg("baho"))["avg"] or 0)
    reyting_soni = LibraryRating.objects.filter(organization=organization).count()
    
    # 2. Faol o'quvchilar soni
    oquvchi_soni = Oquvchi.objects.filter(
        organization=organization, faol=True
    ).count()
    faol_oquvchi_soni = Oquvchi.objects.filter(
        organization=organization, rol="oquvchi", faol=True
    ).count()
    
    # 3. Berish statistiki
    berishlar = Berish.objects.filter(organization=organization)
    berishlar_soni = berishlar.count()
    qaytarilgan_soni = berishlar.filter(qaytarilgan_sana__isnull=False).count()
    
    # 4. Nusxa holati statistiki
    nusxa_holati = Nusxa.objects.filter(organization=organization).aggregate(
        mavjud=Count("id", filter=Q(holati="mavjud")),
        berilgan=Count("id", filter=Q(holati="berilgan")),
        band=Count("id", filter=Q(holati="band")),
        yoqolgan=Count("id", filter=Q(holati="yoqolgan")),
    )
    
    # 5. Baravari hisoblash
    umumiy_bali = round(
        (ortacha_bahol * 0.4 + 
         min(100, faol_oquvchi_soni * 2 + berishlar_soni * 3) * 0.3 + 
         (10 if berishlar_soni > 0 else 0) * 0.3
        , 2)
    )
    if umumiy_bali < 0:
        umumiy_bali = 0
    
    # 6. Ratingni saqlash/update qilish
    rating, created = LibraryRating.objects.update_or_create(
        organization=organization,
        defaults={
            "ortacha": ortacha_bahol,
            "soni": reyting_soni,
            "baho": ortacha_bahol,
            "izoh": f"Haftalik tahlil: {reyting_soni} o'quvchi, {berishlar_soni} berish",
            "yangilangan": timezone.now(),
        }
    )
    
    # 7. LibraryActivityRating (umumiy faollik)
    activity, created = LibraryActivityRating.objects.update_or_create(
        organization=organization,
        defaults={
            "oquvchi_bali": min(100, faol_oquvchi_soni * 2),
            "sinf_bali": min(100, (berishlar_soni // max(oquvchi_soni, 1)) * 3),
            "oqituvchi_bai": min(100, faol_oquvchi_soni * 5),
            "umumiy_bali": umumiy_bali,
            "oquvchi_soni": oquvchi_soni,
            "faol_oquvchi_soni": faol_oquvchi_soni,
            "berishlar_soni": berishlar_soni,
            "qaytarilgan_soni": qaytarilgan_soni,
            "yangilangan": timezone.now(),
        }
    )
    
    return rating, activity


def kitob_qoshilish_reyting_hisobla(kitob_id, organization_id):
    """Yangi kitob qo'shilganda reytingni tezlashtiradi.
    Kitob soni kamida 3 ga yetsa batafsilhisoblab, aks holda keyingi
    hisobot muddatida."""
    
    try:
        kitob = Kitob.objects.get(pk=kitob_id)
        organization = kitob.organization
        
        # Faqat 3 dan ko'p kitob qo'shilganda ko'proq tezlashtirish
        jami_kitob = Kitob.objects.filter(organization=organization).count()
        
        if jami_kitob >= 3:
            _organization_rating_yangilash(organization)
        
        return True
    except Kitob.DoesNotExist:
        return False