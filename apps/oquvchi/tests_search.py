"""PWA/telefon klaviaturasida yozilgan qidiruv ham ishlashi kerak.

Bazadagi ko'plab o'qituvchi ismlarida tipografik apostrof (`‘`, `ʻ`) bor,
telefonda esa oddiy `'` yoziladi. `ChidamliQidiruvFilter` ikkalasini ham
topishi kerak — aks holda o'qituvchi kitob berishda qidiruvda yo'q bo'lib
ko'rinadi.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from config.test_helpers import TenantTestMixin
from .models import Ariza, Oquvchi

User = get_user_model()


class QidiruvBelgilariTest(TenantTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.xodim = User.objects.create_user(
            username="qidiruvchi",
            password="parol12345",
            full_name="Qidiruvchi",
            rol="kutubxonachi",
        )
        self.azolik(self.xodim)
        self.client = APIClient()
        self.client.force_authenticate(self.xodim)

        self.ochetka = Oquvchi.objects.create(
            organization=self.org,
            rol="oqituvchi",
            fish="Jo‘rayeva Nargizaxon",  # U+2018
            telefon="+998901111111",
            karta_raqami="T-1",
            kasb="Matematika",
        )
        self.ganiyeva = Oquvchi.objects.create(
            organization=self.org,
            rol="oqituvchi",
            fish="Gʻaniyeva Gulbahor",  # U+02BB
            telefon="+998902222222",
            karta_raqami="T-2",
            kasb="Tarix",
        )
        self.student = Oquvchi.objects.create(
            organization=self.org,
            rol="oquvchi",
            fish="Ali Valiyev",
            telefon="+998903333333",
            karta_raqami="O-1",
            sinf="7-A",
        )

    def _natijalar(self, url, qidiruv):
        javob = self.client.get(url, {"search": qidiruv})
        self.assertEqual(javob.status_code, 200, javob.data)
        return [x["id"] for x in javob.data["results"]]

    def test_telefondagi_oddiy_apostrof_bilan_topiladi(self):
        natijalar = self._natijalar("/api/readers/", "Jo'rayeva")
        self.assertIn(self.ochetka.pk, natijalar)

    def test_bazadagi_apostrof_bilan_topiladi(self):
        natijalar = self._natijalar("/api/readers/", "Jo‘rayeva")
        self.assertIn(self.ochetka.pk, natijalar)

    def test_boshqa_apostrof_varianti_bilan_topiladi(self):
        self.assertIn(self.ganiyeva.pk, self._natijalar("/api/readers/", "G'aniyeva"))
        self.assertIn(self.ganiyeva.pk, self._natijalar("/api/readers/", "Gʻaniyeva"))

    def test_ikki_soz_bilan_qidiruv_ishlaydi(self):
        self.assertIn(
            self.ochetka.pk,
            self._natijalar("/api/readers/", "Jo'rayeva Nargizaxon"),
        )

    def test_rol_filtri_bilan_birgalikda_ishlaydi(self):
        javob = self.client.get(
            "/api/readers/", {"search": "Jo'rayeva", "rol": "oqituvchi"}
        )
        self.assertEqual(javob.status_code, 200)
        self.assertEqual([x["id"] for x in javob.data["results"]], [self.ochetka.pk])

    def test_ariza_qidiruvida_ham_apostrof_varianti_ishlaydi(self):
        ariza = Ariza.objects.create(
            organization=self.org,
            telegram_id=555111,
            fish="Gʻaniyeva Gulbahor",
            telefon="+998904444444",
            rol="oqituvchi",
            kasb="Geometriya",
        )
        self.assertIn(ariza.pk, self._natijalar("/api/applications/", "G'aniyeva"))

    def test_aralash_qidiruvda_ikki_rol_ham_korinadi(self):
        Ariza.objects.create(
            organization=self.org,
            telegram_id=555222,
            fish="Jo‘rayeva Nargizaxon",
            telefon="+998905555555",
            rol="oqituvchi",
            kasb="Algebra",
        )
        Ariza.objects.create(
            organization=self.org,
            telegram_id=555333,
            fish="Ali Valiyev",
            telefon="+998906666666",
            rol="oquvchi",
            sinf="8-B",
        )
        # Rol filtri yuborilmaganda o'qituvchi va o'quvchi arizalari birga keladi.
        arizalar = self._natijalar("/api/applications/", "")
        self.assertEqual(len(arizalar), 2)
        javob = self.client.get("/api/applications/", {"rol": "oqituvchi"})
        self.assertEqual(javob.data["count"], 1)
        self.assertEqual(javob.data["results"][0]["fish"], "Jo‘rayeva Nargizaxon")
