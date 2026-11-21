"""Profil sahifasidan tanlangan kitobxonlarni o'chirish API testlari."""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from berish.models import Berish
from config.test_helpers import TenantTestMixin
from kitob.models import BandQilish, Kitob
from oquvchi.models import Oquvchi
from organization.models import Organization
from telegrambot.models import OylikStatistika

User = get_user_model()

URL = "/api/readers/ochirish/"


class OquvchilarniOchirishTest(TenantTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.xodim = User.objects.create_user(
            username="kutubxonachi",
            password="parol12345",
            full_name="K",
            rol="kutubxonachi",
        )
        self.azolik(self.xodim)
        self.client.force_authenticate(self.xodim)

    def kitobxon(self, fish, karta, telegram_id=None, rol="oquvchi"):
        return Oquvchi.objects.create(
            fish=fish,
            telefon=f"+99890{karta.split('-')[-1].zfill(7)}",
            telegram_id=telegram_id,
            karta_raqami=karta,
            rol=rol,
            sinf="7-A" if rol == "oquvchi" else "",
            kasb="Matematika" if rol == "oqituvchi" else "",
        )

    def test_toza_kitobxonlarni_ochirish(self):
        ali = self.kitobxon("Ali Valiyev", "K-001", 111)
        vali = self.kitobxon("Vali Valiyev", "K-002", 222)
        qolgan = self.kitobxon("Soli Soliyev", "K-003", 333)

        javob = self.client.post(URL, {"ids": [ali.pk, vali.pk]}, format="json")

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(
            javob.json(), {"ochirildi": 2, "ochirilmadi": []}
        )
        self.assertFalse(Oquvchi.objects.filter(pk__in=[ali.pk, vali.pk]).exists())
        self.assertTrue(Oquvchi.objects.filter(pk=qolgan.pk).exists())

    def test_oqituvchini_ham_ochirish(self):
        muallim = self.kitobxon("Muallim Karimov", "T-001", 444, rol="oqituvchi")
        javob = self.client.post(URL, {"ids": [muallim.pk]}, format="json")
        self.assertEqual(javob.json()["ochirildi"], 1)
        self.assertFalse(Oquvchi.objects.filter(pk=muallim.pk).exists())

    def test_berish_tarixi_bor_kitobxon_ochirilmaydi(self):
        ali = self.kitobxon("Ali Valiyev", "K-001", 111)
        kitob = Kitob.objects.create(
            nomi="O'tkan kunlar", muallif="Abdulla Qodiriy", janr="badiiy", nashr_yili=2015
        )
        Berish.objects.create(
            kitob=kitob,
            oquvchi=ali,
            qaytarish_muddati=date.today() + timedelta(days=10),
        )

        javob = self.client.post(URL, {"ids": [ali.pk]}, format="json")

        self.assertEqual(javob.status_code, 200)
        natija = javob.json()
        self.assertEqual(natija["ochirildi"], 0)
        self.assertEqual(len(natija["ochirilmadi"]), 1)
        self.assertEqual(natija["ochirilmadi"][0]["fish"], "Ali Valiyev")
        self.assertIn("berish", natija["ochirilmadi"][0]["sabab"])
        self.assertTrue(Oquvchi.objects.filter(pk=ali.pk).exists())

    def test_band_qilingan_kitobxon_ochirilmaydi(self):
        ali = self.kitobxon("Ali Valiyev", "K-001", 111)
        kitob = Kitob.objects.create(
            nomi="O'tkan kunlar", muallif="Abdulla Qodiriy", janr="badiiy", nashr_yili=2015
        )
        BandQilish.objects.create(kitob=kitob, oquvchi=ali)

        javob = self.client.post(URL, {"ids": [ali.pk]}, format="json")

        natija = javob.json()
        self.assertEqual(natija["ochirildi"], 0)
        self.assertIn("band", natija["ochirilmadi"][0]["sabab"])
        self.assertTrue(Oquvchi.objects.filter(pk=ali.pk).exists())

    def test_aralash_tanlovda_faqat_tozalar_ochiriladi(self):
        toza = self.kitobxon("Toza Oquvchi", "K-001", 111)
        tarixli = self.kitobxon("Tarixli Oquvchi", "K-002", 222)
        kitob = Kitob.objects.create(
            nomi="O'tkan kunlar", muallif="Abdulla Qodiriy", janr="badiiy", nashr_yili=2015
        )
        BandQilish.objects.create(kitob=kitob, oquvchi=tarixli)

        javob = self.client.post(
            URL, {"ids": [toza.pk, tarixli.pk]}, format="json"
        )

        natija = javob.json()
        self.assertEqual(natija["ochirildi"], 1)
        self.assertEqual(natija["ochirilmadi"][0]["id"], tarixli.pk)
        self.assertFalse(Oquvchi.objects.filter(pk=toza.pk).exists())
        self.assertTrue(Oquvchi.objects.filter(pk=tarixli.pk).exists())

    def test_oy_statistika_bilan_birga_ochiriladi(self):
        ali = self.kitobxon("Ali Valiyev", "K-001", 111)
        OylikStatistika.objects.create(oquvchi=ali, oy=date(2026, 1, 1))

        javob = self.client.post(URL, {"ids": [ali.pk]}, format="json")

        self.assertEqual(javob.json()["ochirildi"], 1)
        self.assertFalse(OylikStatistika.objects.filter(oquvchi_id=ali.pk).exists())

    def test_boshqa_kutubxonaning_kitobxoni_ochirilmaydi(self):
        boshqa = Organization.objects.create(nomi="Boshqa kutubxona")
        begona = Oquvchi.objects.create(
            organization=boshqa,
            fish="Begona Oquvchi",
            telefon="+998905555555",
            karta_raqami="B-001",
            sinf="9-B",
        )
        javob = self.client.post(URL, {"ids": [begona.pk]}, format="json")
        self.assertEqual(javob.json(), {"ochirildi": 0, "ochirilmadi": []})
        self.assertTrue(Oquvchi.objects.filter(pk=begona.pk).exists())

    def test_bosh_kutubxonachi_rad_etiladi(self):
        self.client.force_authenticate(user=None)
        javob = self.client.post(URL, {"ids": [1]}, format="json")
        self.assertEqual(javob.status_code, 401)

    def test_bolmas_ids_rad_etiladi(self):
        javob = self.client.post(URL, {"ids": []}, format="json")
        self.assertEqual(javob.status_code, 400)
