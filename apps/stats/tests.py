"""Kitobxonlar reytingi (sinf va o'qituvchilar) uchun testlar."""
from datetime import timedelta

from django.utils.timezone import now

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from berish.models import Berish
from kitob.models import Kitob
from oquvchi.models import Oquvchi
from organization.models import Membership, Organization

User = get_user_model()


class FaollikReytingiTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            nomi="Test kutubxona", status=Organization.HOLAT_ACTIVE
        )
        self.user = User.objects.create_user(
            username="kutubxonachi", password="parol12345", rol="kutubxonachi"
        )
        Membership.objects.create(
            organization=self.org, user=self.user, rol="egasi", faol=True
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.kitob = Kitob.objects.create(
            organization=self.org,
            nomi="Test kitob",
            muallif="Muallif",
            janr="badiiy",
            nashr_yili=2020,
        )

    def _berish(self, oquvchi, qaytarilgan=True, kitob=None):
        return Berish.objects.create(
            organization=self.org,
            kitob=kitob or self.kitob,
            oquvchi=oquvchi,
            qaytarish_muddati=now().date() + timedelta(days=10),
            qaytarilgan_sana=now().date() if qaytarilgan else None,
        )

    def test_sinf_va_oqituvchilar_reytingi_tartiblangan(self):
        o1 = Oquvchi.objects.create(
            organization=self.org,
            fish="7-A o'quvchi",
            telefon="+998901234567",
            karta_raqami="K1",
            sinf="7-A",
        )
        o2 = Oquvchi.objects.create(
            organization=self.org,
            fish="8-B o'quvchi",
            telefon="+998901234568",
            karta_raqami="K2",
            sinf="8-B",
        )
        oqituvchi = Oquvchi.objects.create(
            organization=self.org,
            rol="oqituvchi",
            fish="Matematika o'qituvchisi",
            telefon="+998901234569",
            karta_raqami="K3",
            kasb="Matematika",
        )

        # 7-A sinfida 2 ta, 8-B da 1 ta, o'qituvchida 1 ta berish.
        self._berish(o1)
        self._berish(o1)
        self._berish(o2)
        self._berish(oqituvchi)

        javob = self.client.get("/api/stats/ratings/activity/")
        self.assertEqual(javob.status_code, 200, javob.data)

        sinflar = javob.data["sinflar"]
        self.assertEqual(len(sinflar), 2)
        self.assertEqual(sinflar[0]["sinf"], "7-A")
        self.assertEqual(sinflar[0]["berishlar"], 2)
        self.assertEqual(sinflar[0]["o_rin"], 1)
        self.assertEqual(sinflar[1]["o_rin"], 2)
        self.assertGreater(sinflar[0]["ball"], 0)

        oqituvchilar = javob.data["oqituvchilar"]
        self.assertEqual(len(oqituvchilar), 1)
        self.assertEqual(oqituvchilar[0]["id"], oqituvchi.pk)
        self.assertEqual(oqituvchilar[0]["fish"], oqituvchi.fish)
        self.assertEqual(oqituvchilar[0]["berishlar"], 1)
        self.assertEqual(oqituvchilar[0]["o_rin"], 1)
        self.assertGreater(oqituvchilar[0]["ball"], 0)

    def test_faol_kitobxonlar_kop_kitob_boyicha_tartiblangan(self):
        o1 = Oquvchi.objects.create(
            organization=self.org,
            fish="7-A birinchi",
            telefon="+998901234567",
            karta_raqami="K1",
            sinf="7-A",
        )
        o2 = Oquvchi.objects.create(
            organization=self.org,
            fish="7-A ikkinchi",
            telefon="+998901234568",
            karta_raqami="K2",
            sinf="7-A",
        )
        oqituvchi = Oquvchi.objects.create(
            organization=self.org,
            rol="oqituvchi",
            fish="Matematika ustozi",
            telefon="+998901234569",
            karta_raqami="K3",
            kasb="Matematika",
        )

        def yangi_kitob(nomi):
            return Kitob.objects.create(
                organization=self.org,
                nomi=nomi,
                muallif="Muallif",
                janr="badiiy",
                nashr_yili=2020,
            )

        # Faol "asli" berishlar bitta kitobga takrorlanmasligi uchun
        # har biriga alohida kitob yaratamiz.
        self._berish(o1, qaytarilgan=False, kitob=yangi_kitob("Kitob 1"))
        self._berish(o1, qaytarilgan=False, kitob=yangi_kitob("Kitob 2"))
        self._berish(o2, qaytarilgan=False, kitob=yangi_kitob("Kitob 3"))
        self._berish(o2, qaytarilgan=True, kitob=yangi_kitob("Kitob 4"))
        self._berish(oqituvchi, qaytarilgan=False, kitob=yangi_kitob("Kitob 5"))

        javob = self.client.get("/api/stats/ratings/activity/")
        self.assertEqual(javob.status_code, 200, javob.data)

        faol_oquvchilar = javob.data["faol_oquvchilar"]
        self.assertEqual(len(faol_oquvchilar), 2)
        self.assertEqual(faol_oquvchilar[0]["id"], o1.pk)
        self.assertEqual(faol_oquvchilar[0]["faol_berishlar"], 2)
        self.assertEqual(faol_oquvchilar[0]["jami_berishlar"], 2)
        self.assertEqual(faol_oquvchilar[0]["sinf"], "7-A")
        self.assertEqual(faol_oquvchilar[0]["o_rin"], 1)
        self.assertEqual(faol_oquvchilar[0]["ball"], 66.7)
        self.assertEqual(faol_oquvchilar[1]["faol_berishlar"], 1)
        self.assertEqual(faol_oquvchilar[1]["jami_berishlar"], 2)

        faol_oqituvchilar = javob.data["faol_oqituvchilar"]
        self.assertEqual(len(faol_oqituvchilar), 1)
        self.assertEqual(faol_oqituvchilar[0]["id"], oqituvchi.pk)
        self.assertEqual(faol_oqituvchilar[0]["kasb"], "Matematika")
        self.assertEqual(faol_oqituvchilar[0]["faol_berishlar"], 1)
        self.assertEqual(faol_oqituvchilar[0]["o_rin"], 1)

    def test_berish_sinfini_qaytaradi(self):
        oquvchi = Oquvchi.objects.create(
            organization=self.org,
            fish="9-V o'quvchi",
            telefon="+998901234567",
            karta_raqami="K1",
            sinf="9-V",
        )
        self._berish(oquvchi)

        javob = self.client.get("/api/loans/")
        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual(javob.data["results"][0]["oquvchi_sinf"], "9-V")


class RecentActivityTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            nomi="Test kutubxona", status=Organization.HOLAT_ACTIVE
        )
        self.xodim = User.objects.create_user(
            username="beruvchi",
            password="parol12345",
            rol="kutubxonachi",
            full_name="Ali Valiyev",
        )
        Membership.objects.create(
            organization=self.org, user=self.xodim, rol="egasi", faol=True
        )
        self.client = APIClient()
        self.client.force_authenticate(self.xodim)
        self.kitob = Kitob.objects.create(
            organization=self.org,
            nomi="Test kitob",
            muallif="Muallif",
            janr="badiiy",
            nashr_yili=2020,
        )
        self.oquvchi = Oquvchi.objects.create(
            organization=self.org,
            fish="7-A o'quvchi",
            telefon="+998901234567",
        )

    def test_songgi_harakatlarda_kim_qilgani_korsatiladi(self):
        Berish.objects.create(
            organization=self.org,
            kitob=self.kitob,
            oquvchi=self.oquvchi,
            bergan_xodim=self.xodim,
            olgan_xodim=self.xodim,
            berilgan_sana=now().date() - timedelta(days=5),
            qaytarish_muddati=now().date() + timedelta(days=10),
            qaytarilgan_sana=now().date(),
        )

        javob = self.client.get("/api/stats/recent-activity/")
        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual(len(javob.data), 2)

        # Qaytarish oxirgi sana bilan birinchi turadi.
        qaytarish = javob.data[0]
        self.assertEqual(qaytarish["turi"], "qaytarish")
        self.assertEqual(qaytarish["sarlavha"], "Kitob qaytarildi")
        self.assertEqual(qaytarish["xodim"], "Ali Valiyev")
        self.assertIn("Test kitob", qaytarish["tavsif"])

        berish = javob.data[1]
        self.assertEqual(berish["turi"], "berish")
        self.assertEqual(berish["sarlavha"], "Kitob berildi")
        self.assertEqual(berish["xodim"], "Ali Valiyev")

    def test_faqat_oz_kutubxonasi_harakatlari_korinadi(self):
        boshqa_org = Organization.objects.create(
            nomi="Boshqa kutubxona", status=Organization.HOLAT_ACTIVE
        )
        boshqa_kitob = Kitob.objects.create(
            organization=boshqa_org,
            nomi="Boshqa kitob",
            muallif="Muallif",
            janr="badiiy",
            nashr_yili=2020,
        )
        boshqa_oquvchi = Oquvchi.objects.create(
            organization=boshqa_org,
            fish="Boshqa o'quvchi",
            telefon="+998901234568",
        )
        Berish.objects.create(
            organization=boshqa_org,
            kitob=boshqa_kitob,
            oquvchi=boshqa_oquvchi,
            bergan_xodim=self.xodim,
            qaytarish_muddati=now().date() + timedelta(days=10),
        )

        javob = self.client.get("/api/stats/recent-activity/")
        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual(len(javob.data), 0)
