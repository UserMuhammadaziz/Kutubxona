"""Oylik shaxsiy statistika (Celery) vazifasi uchun testlar.

Har oyning 1ida 08:00 da (Toshkent vaqti) o'tgan oy bo'yicha har bir
faol o'quvchi/o'qituvchiga shaxsiy statistika yuboriladi. Telegram tarmoqqa
chiqmasligi uchun `telegram_xabar_yubor` mock qilinadi.
"""
from datetime import date
from unittest.mock import patch

from django.test import TestCase

from berish.models import Berish
from config.test_helpers import TenantTestMixin
from kitob.models import Kitob
from oquvchi.models import Oquvchi

from .models import OylikStatistika
from .tasks import oylik_statistika_yubor


class OylikStatistikaTest(TenantTestMixin, TestCase):
    """2026-yil 1-mart — hisobot oyi fevral."""

    def setUp(self):
        super().setUp()

        self.yuborish_patcher = patch(
            "telegrambot.tasks.telegram_xabar_yubor", return_value=True
        )
        self.yuborish = self.yuborish_patcher.start()
        self.addCleanup(self.yuborish_patcher.stop)

        sana_patcher = patch(
            "telegrambot.tasks.timezone.localdate", return_value=date(2026, 3, 1)
        )
        sana_patcher.start()
        self.addCleanup(sana_patcher.stop)

        self.kitob = Kitob.objects.create(
            nomi="O'qish kitobi",
            muallif="Muallif",
            janr="badiiy",
            nashr_yili=2020,
        )
        self.oquvchi = Oquvchi.objects.create(
            fish="Ali Valiyev",
            telefon="+998901234567",
            telegram_id=111111,
            karta_raqami="LIB-2026-0001",
            sinf="7-A",
        )

    def _berish(self, berilgan, muddat, qaytarilgan=None):
        return Berish.objects.create(
            kitob=self.kitob,
            oquvchi=self.oquvchi,
            berilgan_sana=berilgan,
            qaytarish_muddati=muddat,
            qaytarilgan_sana=qaytarilgan,
            holati="qaytarilgan" if qaytarilgan else "faol",
        )

    def _matn(self):
        self.assertTrue(self.yuborish.called)
        return self.yuborish.call_args.args[1]

    def test_otgan_oy_statistikasi_yuboriladi(self):
        self._berish(date(2026, 2, 5), date(2026, 2, 20), date(2026, 2, 18))

        natija = oylik_statistika_yubor()

        self.assertIn("1 ta statistika yuborildi", natija)
        self.yuborish.assert_called_once()
        self.assertEqual(self.yuborish.call_args.args[0], 111111)
        matn = self._matn()
        self.assertIn("Ali Valiyev", matn)
        self.assertIn("fevral", matn)
        self.assertIn("O'qish kitobi", matn)
        self.assertIn("O'tgan oyda o'qigan kitoblaringiz", matn)

        qayd = OylikStatistika.objects.get(oquvchi=self.oquvchi)
        self.assertEqual(qayd.oy, date(2026, 2, 1))
        self.assertTrue(qayd.yuborildi)
        self.assertIsNotNone(qayd.yuborilgan_sana)

    def test_ikkinchi_chaqiruvda_qayta_yuborilmaydi(self):
        oylik_statistika_yubor()
        natija = oylik_statistika_yubor()

        self.assertIn("0 ta statistika yuborildi", natija)
        self.yuborish.assert_called_once()
        self.assertEqual(OylikStatistika.objects.count(), 1)

    def test_kechikkan_qaytarish_qayd_qilinadi(self):
        # 3-fevralda olingan, 10-fevralda qaytarilishi kerak, 15-da qaytarilgan.
        self._berish(date(2026, 2, 3), date(2026, 2, 10), date(2026, 2, 15))
        oylik_statistika_yubor()

        matn = self._matn()
        self.assertIn("Muddatdan kech bergan kitoblaringiz", matn)
        self.assertIn("5 kun kech qaytarildi", matn)

    def test_kechikish_yoq_xabari(self):
        self._berish(date(2026, 2, 3), date(2026, 2, 10), date(2026, 2, 8))
        oylik_statistika_yubor()
        self.assertIn("Muddatdan kechikish kuzatilmadi", self._matn())

    def test_otgan_oydan_oldingi_berish_hisoblanmaydi(self):
        self._berish(date(2026, 1, 25), date(2026, 2, 10), date(2026, 2, 5))
        oylik_statistika_yubor()
        self.assertIn("O'tgan oyda kitob olinmadi", self._matn())

    def test_faol_bolmagan_oquvchiga_yuborilmaydi(self):
        self.oquvchi.faol = False
        self.oquvchi.save(update_fields=["faol"])

        natija = oylik_statistika_yubor()
        self.assertIn("0 ta statistika yuborildi", natija)
        self.yuborish.assert_not_called()
        self.assertEqual(OylikStatistika.objects.count(), 0)

    def test_telegram_id_yoq_oquvchiga_yuborilmaydi(self):
        self.oquvchi.telegram_id = None
        self.oquvchi.save(update_fields=["telegram_id"])

        natija = oylik_statistika_yubor()
        self.assertIn("0 ta statistika yuborildi", natija)
        self.yuborish.assert_not_called()

    def test_yuborish_xatoligi_qayd_qilinadi_va_qayta_uriniladi(self):
        self.yuborish.return_value = False
        natija = oylik_statistika_yubor()
        self.assertIn("0 ta statistika yuborildi, 1 ta yuborilmadi", natija)
        qayd = OylikStatistika.objects.get(oquvchi=self.oquvchi)
        self.assertFalse(qayd.yuborildi)
        self.assertTrue(qayd.xato)

        # Keyingi chaqiruvda muvaffaqiyatsiz yuborish qayta urinadi.
        self.yuborish.return_value = True
        natija = oylik_statistika_yubor()
        self.assertIn("1 ta statistika yuborildi", natija)
        self.assertEqual(OylikStatistika.objects.count(), 1)
        qayd.refresh_from_db()
        self.assertTrue(qayd.yuborildi)
        self.assertEqual(self.yuborish.call_count, 2)

    def test_ocituvchiga_fan_korsatiladi(self):
        self.oquvchi.rol = "oqituvchi"
        self.oquvchi.kasb = "Ona tili"
        self.oquvchi.sinf = ""
        self.oquvchi.save(update_fields=["rol", "kasb", "sinf"])

        oylik_statistika_yubor()
        self.assertIn("Fan: Ona tili", self._matn())
