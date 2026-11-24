"""O'qituvchilarga kitob berish va qaytarish oqimi (web API).

`Oquvchi` modeli o'quvchi/o'qituvchi uchun bitta jadval bo'lgani uchun
berish/qaytarish servislari rolni hisobga olishi shart: o'qituvchi ham
xuddi o'quvchi kabi kitob olib, qaytarishi kerak.
"""
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from config.test_helpers import TenantTestMixin
from kitob.models import Kitob
from nusxa.models import Nusxa
from oquvchi.models import Oquvchi

User = get_user_model()


class OqituvchigaBerishTest(TenantTestMixin, TestCase):
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

        self.oqituvchi = Oquvchi.objects.create(
            rol="oqituvchi",
            fish="Matematika o'qituvchisi",
            telefon="+998901234567",
            telegram_id=111222,
            karta_raqami="T-001",
            kasb="Matematika",
        )
        self.kitob = Kitob.objects.create(
            nomi="O'tkan kunlar", muallif="Abdulla Qodiriy", janr="badiiy", nashr_yili=2015
        )

    def test_nusxasiz_kitobni_oqituvchiga_berib_qaytarish(self):
        with patch("berish.services.telegram_xabar_yubor", return_value=True):
            javob = self.client.post(
                "/api/loans/",
                {"kitob": self.kitob.pk, "oquvchi": self.oqituvchi.pk},
                format="json",
            )
        self.assertEqual(javob.status_code, 201, javob.data)
        berish_id = javob.data["id"]
        self.assertEqual(javob.data["oquvchi_fish"], self.oqituvchi.fish)
        self.assertTrue(javob.data["asli"])

        with patch("berish.services.telegram_xabar_yubor", return_value=True):
            qaytarish = self.client.post(f"/api/loans/{berish_id}/return/", {}, format="json")
        self.assertEqual(qaytarish.status_code, 200, qaytarish.data)
        self.assertEqual(qaytarish.data["oquvchi_telegram_id"], 111222)
        self.assertIsNotNone(qaytarish.data["berish"]["qaytarilgan_sana"])

    def test_nusxa_bilan_kitobni_oqituvchiga_berib_qaytarish(self):
        nusxa = Nusxa.objects.create(
            kitob=self.kitob,
            inventar_raqami="INV-1",
            holati="mavjud",
            qabul_sana=date(2020, 1, 1),
        )
        with patch("berish.services.telegram_xabar_yubor", return_value=True):
            javob = self.client.post(
                "/api/loans/",
                {"nusxa": nusxa.pk, "oquvchi": self.oqituvchi.pk},
                format="json",
            )
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertEqual(javob.data["inventar_raqami"], "INV-1")

        with patch("berish.services.telegram_xabar_yubor", return_value=True):
            qaytarish = self.client.post(f"/api/loans/{javob.data['id']}/return/", {}, format="json")
        self.assertEqual(qaytarish.status_code, 200, qaytarish.data)
        nusxa.refresh_from_db()
        self.assertEqual(nusxa.holati, "mavjud")

    def test_oqituvchi_cheklovlar_bilan_bir_xil_ishlaydi(self):
        """O'qituvchi ham faol kitob limitiga ega (o'quvchi bilan bir xil)."""
        self.org.limit_kitob = 1
        self.org.save(update_fields=["limit_kitob"])

        with patch("berish.services.telegram_xabar_yubor", return_value=True):
            birinchi = self.client.post(
                "/api/loans/",
                {"kitob": self.kitob.pk, "oquvchi": self.oqituvchi.pk},
                format="json",
            )
        self.assertEqual(birinchi.status_code, 201, birinchi.data)

        ikkinchi_kitob = Kitob.objects.create(
            nomi="Navoiy", muallif="Alisher Navoiy", janr="badiiy", nashr_yili=2016
        )
        with patch("berish.services.telegram_xabar_yubor", return_value=True):
            ikkinchi = self.client.post(
                "/api/loans/",
                {"kitob": ikkinchi_kitob.pk, "oquvchi": self.oqituvchi.pk},
                format="json",
            )
        self.assertEqual(ikkinchi.status_code, 400)
        self.assertEqual(ikkinchi.data["error"], "limit_oshdi")

    def test_oqituvchining_oz_kitoblari_meni_endpointida(self):
        with patch("berish.services.telegram_xabar_yubor", return_value=True):
            javob = self.client.post(
                "/api/loans/",
                {"kitob": self.kitob.pk, "oquvchi": self.oqituvchi.pk},
                format="json",
            )
        self.assertEqual(javob.status_code, 201, javob.data)

        javob = self.client.get("/api/loans/my/", {"telegram_id": 111222})
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(len(javob.data), 1)
        self.assertEqual(javob.data[0]["kitob_nomi"], "O'tkan kunlar")
