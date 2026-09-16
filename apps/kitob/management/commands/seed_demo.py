"""
Sinov uchun demo ma'lumot yaratadi:
- Bir nechta kitob va nusxa
- Bir nechta o'quvchi
- Muddati o'tgan (jarimaga tushishi kerak bo'lgan) faol berish
- Barcha nusxalari band bo'lgan kitobga 3 ta o'quvchi bilan navbat

Ishlatish: python manage.py seed_demo
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import now

from berish.models import Berish
from kitob.models import Kitob
from navbat.models import Navbat
from nusxa.models import Nusxa
from oquvchi.models import Oquvchi

User = get_user_model()


class Command(BaseCommand):
    help = "Sinov uchun demo ma'lumot yaratadi (muddati o'tgan berish, navbatda 3 kishi va h.k.)"

    @transaction.atomic
    def handle(self, *args, **options):
        xodim, _ = User.objects.get_or_create(
            username="kutubxonachi_demo",
            defaults={"full_name": "Demo Kutubxonachi", "rol": "kutubxonachi"},
        )
        if not xodim.has_usable_password():
            xodim.set_password("demo12345")
            xodim.save()

        kitob1, _ = Kitob.objects.get_or_create(
            isbn="978-9943-01-001-1",
            defaults=dict(
                nomi="O'tkan kunlar",
                muallif="Abdulla Qodiriy",
                janr="badiiy",
                nashr_yili=1926,
                nashriyot="G'afur G'ulom",
            ),
        )
        kitob2, _ = Kitob.objects.get_or_create(
            isbn="978-9943-01-002-2",
            defaults=dict(
                nomi="Mehrobdan chayon",
                muallif="Abdulla Qodiriy",
                janr="badiiy",
                nashr_yili=1929,
                nashriyot="G'afur G'ulom",
            ),
        )

        nusxa1, _ = Nusxa.objects.get_or_create(
            kitob=kitob1,
            inventar_raqami="INV-000001",
            defaults=dict(holati="berilgan", javon="A-12", qabul_sana=now().date()),
        )
        # kitob2 uchun faqat 1 nusxa, u ham band bo'ladi - navbat sinash uchun
        nusxa2, _ = Nusxa.objects.get_or_create(
            kitob=kitob2,
            inventar_raqami="INV-000002",
            defaults=dict(holati="berilgan", javon="A-13", qabul_sana=now().date()),
        )

        oquvchilar = []
        for i in range(1, 5):
            oquvchi, _ = Oquvchi.objects.get_or_create(
                telefon=f"+99890000000{i}",
                defaults=dict(
                    fish=f"Demo O'quvchi {i}",
                    karta_raqami=f"LIB-{now().year}-000{i}",
                ),
            )
            oquvchilar.append(oquvchi)

        # Muddati o'tgan faol berish (jarima hisoblash uchun)
        Berish.objects.get_or_create(
            nusxa=nusxa1,
            oquvchi=oquvchilar[0],
            defaults=dict(
                bergan_xodim=xodim,
                berilgan_sana=now().date() - timedelta(days=20),
                qaytarish_muddati=now().date() - timedelta(days=6),
                holati="faol",
            ),
        )

        # kitob2 uchun bitta faol berish (nusxa band) + 3 kishi navbatda
        Berish.objects.get_or_create(
            nusxa=nusxa2,
            oquvchi=oquvchilar[1],
            defaults=dict(
                bergan_xodim=xodim,
                berilgan_sana=now().date() - timedelta(days=3),
                qaytarish_muddati=now().date() + timedelta(days=11),
                holati="faol",
            ),
        )
        for oquvchi in oquvchilar[1:4]:
            Navbat.objects.get_or_create(
                kitob=kitob2,
                oquvchi=oquvchi,
                defaults=dict(holati="kutmoqda"),
            )

        self.stdout.write(self.style.SUCCESS(
            "Demo ma'lumot tayyor: 2 kitob, 2 nusxa, 4 o'quvchi, "
            "1 muddati o'tgan berish, kitob2 uchun navbatda 3 kishi."
        ))
