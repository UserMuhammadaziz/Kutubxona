"""Cross-tenant izolyatsiya regress testlari.

Bir kutubxonaning kutubxonachisi boshqa kutubxonaning kitob/jarima/navbat/
arizalarini na ko'ra oladi, na o'zgartira oladi. Bular avval `queryset =
Model.objects.all()` yoki to'g'ridan-to'g'ri `Model.objects...` sabab oshkor
bo'lgan.
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from berish.models import Berish
from jarima.models import Jarima
from kitob.models import Kitob
from navbat.models import Navbat
from oquvchi.models import Ariza, Oquvchi
from organization.models import Membership, Organization

User = get_user_model()


class CrossTenantIsolationTest(TestCase):
    def setUp(self):
        self.org_a = Organization.objects.create(
            nomi="A kutubxona", slug="tenant-a", status=Organization.HOLAT_ACTIVE
        )
        self.org_b = Organization.objects.create(
            nomi="B kutubxona", slug="tenant-b", status=Organization.HOLAT_ACTIVE
        )
        self.xodim = User.objects.create_user(
            username="tenant_b_xodim", password="parol12345", rol="kutubxonachi"
        )
        Membership.objects.create(
            organization=self.org_b, user=self.xodim, rol="kutubxonachi", faol=True
        )
        self.client = APIClient()
        self.client.force_authenticate(self.xodim)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org_b.pk))

        self.kitob_a = Kitob.objects.create(
            organization=self.org_a,
            nomi="Maxfiy kitob",
            muallif="A Muallif",
            janr="badiiy",
            nashr_yili=2020,
            isbn="AAA-111",
        )
        self.kitob_b = Kitob.objects.create(
            organization=self.org_b,
            nomi="Ochiq kitob",
            muallif="B Muallif",
            janr="ilmiy",
            nashr_yili=2021,
            isbn="BBB-222",
        )
        self.oquvchi_a = Oquvchi.objects.create(
            organization=self.org_a,
            rol="oquvchi",
            fish="A Oquvchi",
            telefon="+998901000001",
            sinf="7-A",
            telegram_id=100001,
        )
        self.oquvchi_b = Oquvchi.objects.create(
            organization=self.org_b,
            rol="oquvchi",
            fish="B Oquvchi",
            telefon="+998901000002",
            sinf="8-B",
            telegram_id=100002,
        )

    def test_kitob_qidiruvi_faqat_oz_kutubxonasini_korsatadi(self):
        javob = self.client.get("/api/books/search/", {"q": "Maxfiy"})
        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual([x["id"] for x in javob.data], [])

        javob = self.client.get("/api/books/search/", {"q": "Ochiq"})
        self.assertEqual([x["id"] for x in javob.data], [self.kitob_b.pk])

        janrlar = self.client.get("/api/books/genres/")
        self.assertEqual(janrlar.status_code, 200, janrlar.data)
        self.assertNotIn("badiiy", [x["key"] for x in janrlar.data])

    def test_jarima_boshqa_kutubxonada_korinmaydi_va_tolanmaydi(self):
        berish = Berish.objects.create(
            organization=self.org_a,
            kitob=self.kitob_a,
            oquvchi=self.oquvchi_a,
            qaytarish_muddati=date.today() - timedelta(days=3),
        )
        jarima = Jarima.objects.create(
            organization=self.org_a,
            berish=berish,
            kechikkan_kunlar=3,
            summa=15000,
        )
        royxat = self.client.get("/api/fines/")
        self.assertEqual(royxat.status_code, 200, royxat.data)
        self.assertNotIn(jarima.pk, [x["id"] for x in royxat.data["results"]])

        javob = self.client.post(f"/api/fines/{jarima.pk}/pay/")
        self.assertEqual(javob.status_code, 404, javob.data)
        jarima.refresh_from_db()
        self.assertFalse(jarima.tolandimi)

    def test_navbat_boshqa_kutubxonada_korinmaydi_va_ochirilmaydi(self):
        navbat = Navbat.objects.create(
            organization=self.org_a, kitob=self.kitob_a, oquvchi=self.oquvchi_a
        )
        royxat = self.client.get("/api/reservations/")
        self.assertEqual(royxat.status_code, 200, royxat.data)
        self.assertNotIn(navbat.pk, [x["id"] for x in royxat.data["results"]])

        javob = self.client.delete(f"/api/reservations/{navbat.pk}/")
        self.assertEqual(javob.status_code, 404, javob.data)
        self.assertTrue(Navbat.objects.filter(pk=navbat.pk).exists())

    def test_ariza_boshqa_kutubxonada_korinmaydi_va_tasdiqlanmaydi(self):
        ariza = Ariza.objects.create(
            organization=self.org_a,
            telegram_id=200001,
            fish="A Ariza",
            telefon="+998901000003",
            rol="oquvchi",
            sinf="9-A",
        )
        royxat = self.client.get("/api/applications/")
        self.assertEqual(royxat.status_code, 200, royxat.data)
        self.assertNotIn(ariza.pk, [x["id"] for x in royxat.data["results"]])

        javob = self.client.post(f"/api/applications/{ariza.pk}/approve/")
        self.assertEqual(javob.status_code, 404, javob.data)
        ariza.refresh_from_db()
        self.assertEqual(ariza.holati, "kutmoqda")

    def test_ariza_yaratish_boshqa_tenant_arizasini_ochirmaydi(self):
        ariza = Ariza.objects.create(
            organization=self.org_a,
            telegram_id=200002,
            fish="Eski A Ariza",
            telefon="+998901000004",
            rol="oquvchi",
            sinf="9-B",
            holati="rad_etildi",
        )
        javob = self.client.post(
            "/api/applications/",
            {
                "telegram_id": 200002,
                "fish": "Yangi B Ariza",
                "telefon": "+998901000005",
                "rol": "oquvchi",
                "sinf": "10-A",
            },
            format="json",
        )
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertTrue(Ariza.objects.filter(pk=ariza.pk).exists())

    def test_telegram_id_bilan_boshqa_kutubxonaning_malumoti_ochilmaydi(self):
        javob = self.client.get("/api/holds/my/", {"telegram_id": self.oquvchi_a.telegram_id})
        self.assertEqual(javob.status_code, 404, javob.data)
        javob = self.client.get("/api/loans/my/", {"telegram_id": self.oquvchi_a.telegram_id})
        self.assertEqual(javob.status_code, 404, javob.data)
