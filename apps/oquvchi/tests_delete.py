"""Profil sahifasidan tanlangan kitobxonlarni o'chirish API testlari."""
from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from berish.models import Berish
from config.test_helpers import TenantTestMixin
from kitob.models import BandQilish, Kitob
from oquvchi.models import Ariza, Oquvchi
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
            javob.json(), {"status": True, "ochirildi": 2, "ochirilmadi": []}
        )
        self.assertFalse(Oquvchi.objects.filter(pk__in=[ali.pk, vali.pk]).exists())
        self.assertTrue(Oquvchi.objects.filter(pk=qolgan.pk).exists())

    def test_oqituvchini_ham_ochirish(self):
        muallim = self.kitobxon("Muallim Karimov", "T-001", 444, rol="oqituvchi")
        javob = self.client.post(URL, {"ids": [muallim.pk]}, format="json")
        self.assertEqual(javob.json()["ochirildi"], 1)
        self.assertFalse(Oquvchi.objects.filter(pk=muallim.pk).exists())

    def test_qaytarilgan_berish_va_eski_band_bilan_ochiriladi(self):
        """Bandlar bo'limida ko'rinmaydigan tarix endi to'siq bo'lmasligi kerak."""
        ali = self.kitobxon("Ali Valiyev", "K-001", 111)
        kitob = Kitob.objects.create(
            nomi="O'tkan kunlar", muallif="Abdulla Qodiriy", janr="badiiy", nashr_yili=2015
        )
        berish = Berish.objects.create(
            kitob=kitob,
            oquvchi=ali,
            qaytarish_muddati=date.today() - timedelta(days=5),
            qaytarilgan_sana=date.today() - timedelta(days=2),
        )
        band = BandQilish.objects.create(kitob=kitob, oquvchi=ali, holati="tasdiqlandi")
        band.berish = berish
        band.save(update_fields=["berish"])
        BandQilish.objects.create(kitob=kitob, oquvchi=ali, holati="bekor_qilindi")

        javob = self.client.post(URL, {"ids": [ali.pk]}, format="json")

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.json(), {"status": True, "ochirildi": 1, "ochirilmadi": []})
        self.assertFalse(Oquvchi.objects.filter(pk=ali.pk).exists())
        self.assertFalse(BandQilish.objects.filter(oquvchi_id=ali.pk).exists())
        self.assertFalse(Berish.objects.filter(oquvchi_id=ali.pk).exists())

    def test_qaytarilmagan_kitob_bor_kitobxon_ochirilmaydi(self):
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

        natija = javob.json()
        self.assertEqual(natija["ochirildi"], 0)
        self.assertIn("qaytarilmagan", natija["ochirilmadi"][0]["sabab"])
        self.assertTrue(Oquvchi.objects.filter(pk=ali.pk).exists())

    def test_faqat_kutmoqdagi_band_toshiq_qiladi(self):
        ali = self.kitobxon("Ali Valiyev", "K-001", 111)
        kitob = Kitob.objects.create(
            nomi="O'tkan kunlar", muallif="Abdulla Qodiriy", janr="badiiy", nashr_yili=2015
        )
        BandQilish.objects.create(kitob=kitob, oquvchi=ali, holati="rad_etildi")

        javob = self.client.post(URL, {"ids": [ali.pk]}, format="json")

        self.assertEqual(javob.json()["ochirildi"], 1)
        self.assertFalse(Oquvchi.objects.filter(pk=ali.pk).exists())

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
        self.assertEqual(javob.json(), {"status": True, "ochirildi": 0, "ochirilmadi": []})
        self.assertTrue(Oquvchi.objects.filter(pk=begona.pk).exists())

    def test_bosh_kutubxonachi_rad_etiladi(self):
        self.client.force_authenticate(user=None)
        javob = self.client.post(URL, {"ids": [1]}, format="json")
        self.assertEqual(javob.status_code, 401)

    def test_bolmas_ids_rad_etiladi(self):
        javob = self.client.post(URL, {"ids": []}, format="json")
        self.assertEqual(javob.status_code, 400)

    # --- O'chirish haqidagi xabar va qayta ariza oqimi --------------------

    @patch("oquvchi.services.telegram_xabar_yubor", return_value=True)
    def test_ochirilganda_qayta_ariza_xabari_yuboriladi(self, yuborish):
        ali = self.kitobxon("Ali Valiyev", "K-001", 111)
        with self.captureOnCommitCallbacks(execute=True):
            javob = self.client.post(URL, {"ids": [ali.pk]}, format="json")

        self.assertEqual(javob.json()["ochirildi"], 1)
        self.assertEqual(yuborish.call_count, 1)
        args, kwargs = yuborish.call_args
        self.assertEqual(args[0], 111)
        self.assertIn("/start", args[1])
        self.assertIn("a'riza", args[1])
        self.assertEqual(kwargs["organization"].pk, self.org.pk)

    @patch("oquvchi.services.telegram_xabar_yubor", return_value=True)
    def test_ikki_kitobxonga_ikkita_xabar_yuboriladi(self, yuborish):
        ali = self.kitobxon("Ali Valiyev", "K-001", 111)
        vali = self.kitobxon("Vali Valiyev", "K-002", 222)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(URL, {"ids": [ali.pk, vali.pk]}, format="json")

        self.assertEqual(
            sorted(call.args[0] for call in yuborish.call_args_list), [111, 222]
        )

    @patch("oquvchi.services.telegram_xabar_yubor", return_value=True)
    def test_telegramsiz_kitobxonga_xabar_yuborilmaydi(self, yuborish):
        ali = self.kitobxon("Ali Valiyev", "K-001")
        with self.captureOnCommitCallbacks(execute=True):
            javob = self.client.post(URL, {"ids": [ali.pk]}, format="json")

        self.assertEqual(javob.json()["ochirildi"], 1)
        yuborish.assert_not_called()

    @patch("oquvchi.services.telegram_xabar_yubor", return_value=True)
    def test_ochirilmagan_kitobxonga_xabar_yuborilmaydi(self, yuborish):
        """Joriy kitobi bor kitobxon o'chirilmagani uchun xabar ham ketmaydi."""
        ali = self.kitobxon("Ali Valiyev", "K-001", 111)
        kitob = Kitob.objects.create(
            nomi="O'tkan kunlar", muallif="Abdulla Qodiriy", janr="badiiy", nashr_yili=2015
        )
        Berish.objects.create(
            kitob=kitob,
            oquvchi=ali,
            qaytarish_muddati=date.today() + timedelta(days=10),
        )
        with self.captureOnCommitCallbacks(execute=True):
            javob = self.client.post(URL, {"ids": [ali.pk]}, format="json")

        self.assertEqual(javob.json()["ochirildi"], 0)
        yuborish.assert_not_called()

    @patch("oquvchi.services.telegram_xabar_yubor", return_value=True)
    def test_eski_ariza_tozalanib_qayta_ariza_yuborish_ishlaydi(self, yuborish):
        """Bot '/start' da 'kutmoqda' deb bloklanmasligi kerak."""
        ali = self.kitobxon("Ali Valiyev", "K-001", 111)
        Ariza.objects.create(
            telegram_id=111,
            fish="Ali Valiyev",
            telefon="+998901111111",
            sinf="7-A",
            holati="kutmoqda",
        )
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(URL, {"ids": [ali.pk]}, format="json")

        self.assertFalse(Ariza.objects.filter(telegram_id=111).exists())
        holat = self.client.get("/api/applications/status/", {"telegram_id": 111})
        self.assertIsNone(holat.json()["holati"])

        yangi = self.client.post(
            "/api/applications/",
            {
                "telegram_id": 111,
                "fish": "Ali Valiyev",
                "telefon": "+998901111111",
                "sinf": "8-B",
            },
            format="json",
        )
        self.assertEqual(yangi.status_code, 201, yangi.data)
