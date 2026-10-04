"""Kitobni band qilish (saqlab qo'yish) oqimi testlari.

Talab: o'quvchi/o'qituvchi kitobni band qilgandan keyin u hech kimga
berilmaydi; faqat kutubxonachi yoki administrator tasdiqlagandan keyin
so'rov qiluvchiga Berish yozuvi bilan beriladi.

* `BandBerishHimoyasiTest` - tasdiqlanmaguncha berish bloklanadi.
* `BandTasdiqlashTest` - tasdiqlash kitobni so'rovchiga beradi.
* `BandRuxsatTest` - tasdiqlash faqat kutubxonachi/administratorga ochiq.
* `BandApiTest` - API endpoint'lari (so'rov, tasdiqlash, rad, bekor, `my`).
* `BolimlarAjratishTest` - «O'quvchilar» va «O'qituvchilar» rol filtri.
"""
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from berish.models import Berish
from berish.services import kitob_ber
from kitob.models import BandQilish, Kitob
from kitob.serializers import BandQilishSerializer
from kitob.services import (
    band_qilish,
    band_qilishni_bekor_qil,
    band_qilishni_rad_et,
    band_qilishni_tasdiqla,
    faol_band_bormi,
)
from navbat.models import Navbat
from navbat.services import navbatga_qosh, navbatni_mavjud_nusxa_bilan_ishga_tushir
from nusxa.models import Nusxa
from oquvchi.models import Oquvchi

User = get_user_model()


class BandTestBase(TestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.xodim = User.objects.create_user(
            username="kutubxonachi", password="parol12345", full_name="K", rol="kutubxonachi"
        )
        self.admin = User.objects.create_user(
            username="admin", password="parol12345", full_name="A", rol="administrator"
        )
        self.kitob = Kitob.objects.create(
            nomi="O'tkan kunlar", muallif="Abdulla Qodiriy", janr="badiiy", nashr_yili=2015
        )
        self.nusxa = Nusxa.objects.create(
            kitob=self.kitob,
            inventar_raqami="INV-1",
            holati="mavjud",
            qabul_sana=date(2020, 1, 1),
        )
        self.oquvchi = Oquvchi.objects.create(
            fish="Alisher", telefon="+998901234567", telegram_id=111, karta_raqami="K-1"
        )
        self.ikkinchi = Oquvchi.objects.create(
            fish="Bekzod", telefon="+998901234568", telegram_id=222, karta_raqami="K-2"
        )

    def url(self, nomi, *args):
        return reverse(nomi, args=args)

    def kirish(self, user=None):
        self.client.force_authenticate(user=user or self.xodim)


class BandBerishHimoyasiTest(BandTestBase):
    """Band qilingan kitob tasdiqlanmaguncha berilmasligi kerak."""

    def test_band_qilinganda_kitob_berilmaydi(self):
        band_qilish(self.kitob, self.oquvchi)

        with self.assertRaises(ValidationError) as ctx:
            kitob_ber(self.nusxa, self.oquvchi, self.xodim)

        self.assertEqual(ctx.exception.detail["error"], "kitob_band_qilingan")
        self.nusxa.refresh_from_db()
        self.assertEqual(self.nusxa.holati, "mavjud")
        self.assertFalse(Berish.objects.exists())

    def test_boshqa_oquvchiga_ham_berilmaydi(self):
        """Band qilingan kitobni boshqa o'quvchi ham olmaydi."""
        band_qilish(self.kitob, self.oquvchi)

        with self.assertRaises(ValidationError):
            kitob_ber(self.nusxa, self.ikkinchi, self.xodim)

        self.assertFalse(Berish.objects.exists())

    def test_xodim_ham_tasdiqlashdan_oldin_bera_olmaydi(self):
        """Tasdiqlash butunlay alohida qadam: oddiy berish ham bloklanadi."""
        band_qilish(self.kitob, self.oquvchi)

        with self.assertRaises(ValidationError):
            kitob_ber(self.nusxa, self.oquvchi, self.xodim)

        self.assertFalse(Berish.objects.exists())

    def test_berish_xatosi_kitobni_navbatga_qoshmaydi(self):
        """Kitob band bo'lsa, o'quvchi navbatga tushib ketmasin — aks holda
        tasdiqlangandan keyin navbatdagi odamga ham taklif yuborilardi."""
        band_qilish(self.kitob, self.ikkinchi)

        with self.assertRaises(ValidationError):
            from berish.services import kitob_ber_by_kitob

            kitob_ber_by_kitob(self.kitob, self.oquvchi, self.xodim)

        self.assertFalse(Navbat.objects.exists())

    def test_bitta_kitobga_ikki_band_qilinmaydi(self):
        band_qilish(self.kitob, self.oquvchi)

        with self.assertRaises(ValidationError) as ctx:
            band_qilish(self.kitob, self.ikkinchi)

        self.assertEqual(ctx.exception.detail["error"], "allaqachon_band_qilingan")
        self.assertEqual(BandQilish.objects.filter(holati="kutmoqda").count(), 1)

    def test_bir_oquvchi_ikki_marta_so_rov_qilsa_idempotent(self):
        band, yangi = band_qilish(self.kitob, self.oquvchi)
        yana, yana_yangi = band_qilish(self.kitob, self.oquvchi)

        self.assertTrue(yangi)
        self.assertFalse(yana_yangi)
        self.assertEqual(band.pk, yana.pk)
        self.assertEqual(BandQilish.objects.count(), 1)

    def test_band_berilgan_kitobga_qilinmaydi(self):
        kitob_ber(self.nusxa, self.oquvchi, self.xodim)

        with self.assertRaises(ValidationError) as ctx:
            band_qilish(self.kitob, self.oquvchi)

        self.assertEqual(ctx.exception.detail["error"], "allaqachon_berilgan")

    def test_rad_qilingach_kitob_yana_beriladi(self):
        band = band_qilish(self.kitob, self.oquvchi)[0]
        band_qilishni_rad_et(band, self.xodim)

        berish = kitob_ber(self.nusxa, self.oquvchi, self.xodim)

        self.assertIsNotNone(berish.pk)
        self.assertFalse(faol_band_bormi(self.kitob.pk))

    def test_bekor_qilingach_kitob_yana_beriladi(self):
        band = band_qilish(self.kitob, self.oquvchi)[0]
        band_qilishni_bekor_qil(band, self.oquvchi)

        berish = kitob_ber(self.nusxa, self.oquvchi, self.xodim)
        self.assertIsNotNone(berish.pk)

    def test_band_qilingan_kitobga_taklif_yuborilmaydi(self):
        """Band qilingan kitob navbatdagi odamga taklif qilinmasin."""
        band_qilish(self.kitob, self.oquvchi)
        navbatga_qosh(self.kitob, self.ikkinchi)

        self.assertFalse(navbatni_mavjud_nusxa_bilan_ishga_tushir(self.kitob.pk))
        self.assertEqual(Navbat.objects.get().holati, "kutmoqda")


class BandTasdiqlashTest(BandTestBase):
    def test_tasdiqlash_kitobni_so_rovchiga_beradi(self):
        band = band_qilish(self.kitob, self.oquvchi, "Darsga tayyorlanish")[0]

        band, berish = band_qilishni_tasdiqla(band, self.xodim, "Tasdiqlandi")

        self.assertEqual(band.holati, "tasdiqlandi")
        self.assertEqual(band.tasdiqlovchi, self.xodim)
        self.assertEqual(berish.oquvchi, self.oquvchi)
        self.assertEqual(berish.holati, "faol")
        self.assertEqual(band.berish_id, berish.pk)
        self.nusxa.refresh_from_db()
        self.assertEqual(self.nusxa.holati, "berilgan")
        self.assertFalse(faol_band_bormi(self.kitob.pk))

    def test_administrator_tasdiqlay_oladi(self):
        band = band_qilish(self.kitob, self.oquvchi)[0]

        band, berish = band_qilishni_tasdiqla(band, self.admin)

        self.assertEqual(band.holati, "tasdiqlandi")
        self.assertEqual(berish.oquvchi, self.oquvchi)

    def test_berish_qoidasi_tasdiqlashda_ham_ishlaydi(self):
        """Tasdiqlash «oddiy berish» qoidalarini chetlab o'tmaydi:
        limit/jarima/bloklangan o'quvchiga tasdiqlash ham xato beradi."""
        band = band_qilish(self.kitob, self.oquvchi)[0]
        self.oquvchi.faol = False
        self.oquvchi.save(update_fields=["faol"])

        with self.assertRaises(ValidationError):
            band_qilishni_tasdiqla(band, self.xodim)

        band.refresh_from_db()
        self.assertEqual(band.holati, "kutmoqda")
        self.assertFalse(Berish.objects.exists())

    def test_ikki_marta_tasdiqlab_bolmaydi(self):
        band = band_qilish(self.kitob, self.oquvchi)[0]
        band_qilishni_tasdiqla(band, self.xodim)

        with self.assertRaises(ValidationError) as ctx:
            band_qilishni_tasdiqla(band, self.xodim)

        self.assertEqual(ctx.exception.detail["error"], "so_rov_yopilgan")
        self.assertEqual(Berish.objects.count(), 1)

    def test_barcha_nusxalar_berilgan_bolsa_tasdiqlash_toxtaydi(self):
        """Tasdiqlash — berish; agar berish mumkin bo'lmasa, so'rov
        kutilayotgan holatda qolishi kerak (javob berish emas)."""
        band = band_qilish(self.kitob, self.oquvchi)[0]
        self.nusxa.holati = "berilgan"
        self.nusxa.save(update_fields=["holati"])

        with self.assertRaises(ValidationError) as ctx:
            band_qilishni_tasdiqla(band, self.xodim)

        self.assertEqual(ctx.exception.detail["error"], "berish_mumkin_emas")
        band.refresh_from_db()
        self.assertEqual(band.holati, "kutmoqda")
        self.assertIsNone(band.berish_id)


class BandRuxsatTest(BandTestBase):
    def test_anonim_tasdiqlay_olmaydi(self):
        band = band_qilish(self.kitob, self.oquvchi)[0]

        javob = self.client.post(self.url("holds-approve", band.pk))

        self.assertIn(javob.status_code, (401, 403))
        band.refresh_from_db()
        self.assertEqual(band.holati, "kutmoqda")
        self.assertFalse(Berish.objects.exists())

    def test_oddiy_kutubxonachi_kitobni_olmaydi(self):
        """Bot xizmat akkaunti `kutubxonachi` roli bilan kiradi."""
        band = band_qilish(self.kitob, self.oquvchi)[0]

        self.kirish(user=self.ikkinchi_kutubxonachi())
        javob = self.client.post(self.url("holds-approve", band.pk))

        self.assertEqual(javob.status_code, 403)

    def ikkinchi_kutubxonachi(self):
        return User.objects.create_user(
            username="kutubxonachi2", password="parol12345", full_name="K2", rol="oqituvchi"
        )


class BandApiTest(BandTestBase):
    def test_createsovrov_telegram_id_bilan(self):
        self.kirish()

        javob = self.client.post(
            self.url("holds-list"),
            {"kitob": self.kitob.pk, "telegram_id": self.oquvchi.telegram_id, "izoh": "dars"},
            content_type="application/json",
        )

        self.assertEqual(javob.status_code, 201)
        self.assertEqual(javob.data["holati"], "kutmoqda")
        self.assertEqual(javob.data["oquvchi_fish"], "Alisher")
        self.assertTrue(BandQilish.objects.exists())

    def test_so_rov_anonim_rad_qilinadi(self):
        javob = self.client.post(
            self.url("holds-list"),
            {"kitob": self.kitob.pk, "telegram_id": self.oquvchi.telegram_id},
            content_type="application/json",
        )

        self.assertIn(javob.status_code, (401, 403))
        self.assertFalse(BandQilish.objects.exists())

    def test_tasdiqlash_berish_yozuvi_yaratadi(self):
        band = band_qilish(self.kitob, self.oquvchi)[0]
        self.kirish(self.admin)

        javob = self.client.post(
            self.url("holds-approve", band.pk), {"izoh": "ruxsat"}, content_type="application/json"
        )

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["holati"], "tasdiqlandi")
        self.assertIsNotNone(javob.data["berish"])
        self.assertEqual(Berish.objects.count(), 1)

    def test_rad_etish_kitobni_ochadi(self):
        band = band_qilish(self.kitob, self.oquvchi)[0]
        self.kirish()

        javob = self.client.post(
            self.url("holds-reject", band.pk), {"izoh": "kerak emas"}, content_type="application/json"
        )

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["holati"], "rad_etildi")
        self.assertFalse(Berish.objects.exists())
        self.assertFalse(faol_band_bormi(self.kitob.pk))

    def test_mening_so_rovlarim(self):
        band_qilish(self.kitob, self.oquvchi)
        self.kirish()

        javob = self.client.get(
            self.url("holds-meni"), {"telegram_id": self.oquvchi.telegram_id}
        )

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(len(javob.data), 1)
        self.assertEqual(javob.data[0]["kitob_nomi"], "O'tkan kunlar")

    def test_bekor_qilish(self):
        band = band_qilish(self.kitob, self.oquvchi)[0]
        self.kirish()

        javob = self.client.post(
            self.url("holds-cancel", band.pk),
            {"telegram_id": self.oquvchi.telegram_id},
            content_type="application/json",
        )

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["holati"], "bekor_qilindi")

    def test_boshqasining_so_rovini_bekor_qilib_bolmaydi(self):
        band = band_qilish(self.kitob, self.oquvchi)[0]
        self.kirish()

        javob = self.client.post(
            self.url("holds-cancel", band.pk),
            {"telegram_id": self.ikkinchi.telegram_id},
            content_type="application/json",
        )

        self.assertEqual(javob.status_code, 400)
        band.refresh_from_db()
        self.assertEqual(band.holati, "kutmoqda")

    def test_kutubxonachilar_ro_yxati(self):
        band_qilish(self.kitob, self.oquvchi)
        self.kirish()

        javob = self.client.get(self.url("holds-list"))

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(len(javob.data["results"]), 1)

    def test_ro_yxat_paginated_shaklda_qaytadi(self):
        """Frontend ro'yxatni `{count, results}` shaklda kutadi.

        Avval endpoint oddiy list qaytarardi, frontend esa `data.results`
        o'qigani uchun «Bandlar» sahifasi doim bo'sh ko'rinardi."""
        band_qilish(self.kitob, self.oquvchi)
        self.kirish()

        javob = self.client.get(self.url("holds-list"))

        self.assertEqual(javob.status_code, 200)
        self.assertIsInstance(javob.data, dict)
        self.assertIn("count", javob.data)
        self.assertIn("results", javob.data)
        self.assertEqual(javob.data["count"], 1)
        self.assertEqual(javob.data["results"][0]["kitob_nomi"], self.kitob.nomi)

    def test_kitob_id_bilan_saralanadi(self):
        band_qilish(self.kitob, self.oquvchi)
        boshqa_kitob = Kitob.objects.create(
            nomi="Boshqa kitob", muallif="M", janr="badiiy", nashr_yili=2020
        )
        band_qilish(boshqa_kitob, self.oquvchi)
        self.kirish()

        javob = self.client.get(self.url("holds-list"), {"kitob": self.kitob.id})

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["count"], 1)
        self.assertEqual(javob.data["results"][0]["kitob_nomi"], self.kitob.nomi)

    def test_kitob_maydoni_raqam_bo_lmasa_xato_qaytarmaydi(self):
        """Qidiruv maydoniga nom yozilsa 500 chiqmasligi kerak."""
        band_qilish(self.kitob, self.oquvchi)
        self.kirish()

        javob = self.client.get(self.url("holds-list"), {"kitob": "Alpomish"})

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["count"], 1)

    def test_holati_bilan_saralanadi(self):
        band_qilish(self.kitob, self.oquvchi)
        self.kirish()

        javob = self.client.get(self.url("holds-list"), {"holati": "kutmoqda"})

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["count"], 1)

    def test_boshqa_holat_boya_ro_yxat_bosh(self):
        band_qilish(self.kitob, self.oquvchi)
        self.kirish()

        javob = self.client.get(self.url("holds-list"), {"holati": "rad_etildi"})

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["count"], 0)
        self.assertEqual(javob.data["results"], [])

    def test_sahifalash_parametri_ishlaydi(self):
        band_qilish(self.kitob, self.oquvchi)
        self.kirish()

        javob = self.client.get(self.url("holds-list"), {"page": 1})

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["count"], 1)

    def test_oddiy_foydalanuvchi_ro_yxatni_kura_olmaydi(self):
        band_qilish(self.kitob, self.oquvchi)[0]
        self.kirish(self.ikkinchi_kutubxonachi())

        javob = self.client.get(self.url("holds-list"))

        self.assertEqual(javob.status_code, 403)

    def ikkinchi_kutubxonachi(self):
        return User.objects.create_user(
            username="kutubxonachi2", password="parol12345", full_name="K2", rol="oqituvchi"
        )


class BolimlarAjratishTest(BandTestBase):
    """«O'quvchilar» va «O'qituvchilar» bo'limlari aralashmasligi."""

    def setUp(self):
        super().setUp()
        self.oqituvchi = Oquvchi.objects.create(
            fish="Ustoz", telefon="+998901234569", telegram_id=333,
            karta_raqami="K-3", rol="oqituvchi", kasb="Matematika",
        )
        self.kirish()

    def test_oquvchilar_bo_limi_faqat_oquvchi(self):
        javob = self.client.get(self.url("readers-list"), {"rol": "oquvchi"})

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(sorted(r["fish"] for r in javob.data["results"]), ["Alisher", "Bekzod"])

    def test_oqituvchilar_bo_limi_faqat_oqituvchi(self):
        javob = self.client.get(self.url("readers-list"), {"rol": "oqituvchi"})

        self.assertEqual(javob.status_code, 200)
        self.assertEqual([r["fish"] for r in javob.data["results"]], ["Ustoz"])


class BandTasdiqlovchiTest(BandTestBase):
    """«Tasdiqlovchi» ustuni haqiqiy ismni ko'rsatishi kerak.

    Loyihada xodimlar `User.full_name` bilan saqlanadi; `first_name`/`last_name`
    bo'sh. Serializer avval `tasdiqlovchi.get_full_name()` ishlatardi, bu
    `AbstractUser` metodi bo'sh `first_name last_name` yig'indisi qaytaradi —
    natijada ustun doim bo'sh ko'rinardi.
    """

    def test_tasdiqlashdan_keyin_tasdiqlovchi_ismi_korunadi(self):
        self.xodim.full_name = "Alisher Karimov"
        self.xodim.save(update_fields=["full_name"])
        band = band_qilish(self.kitob, self.oquvchi)[0]

        band_qilishni_tasdiqla(band, self.xodim)

        band.refresh_from_db()
        ma_lumot = BandQilishSerializer(band).data
        self.assertEqual(ma_lumot["tasdiqlovchi_fish"], "Alisher Karimov")

    def test_tasdiqlanmagan_so_rovda_tasdiqlovchi_bosh(self):
        band = band_qilish(self.kitob, self.oquvchi)[0]

        ma_lumot = BandQilishSerializer(band).data

        self.assertEqual(ma_lumot["tasdiqlovchi_fish"], "")

    def test_api_royxatda_tasdiqlovchi_ismi_keladi(self):
        self.xodim.full_name = "Alisher Karimov"
        self.xodim.save(update_fields=["full_name"])
        band = band_qilish(self.kitob, self.oquvchi)[0]
        band_qilishni_tasdiqla(band, self.xodim)
        self.kirish()

        javob = self.client.get(self.url("holds-list"), {"holati": "tasdiqlandi"})

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["count"], 1)
        self.assertEqual(javob.data["results"][0]["tasdiqlovchi_fish"], "Alisher Karimov")

    def test_full_name_bosh_bo_lsa_username_ko_rsatiladi(self):
        """`full_name` bo'sh bo'lsa ham ustun bo'sh qolmasligi kerak."""
        self.xodim.full_name = ""
        self.xodim.save(update_fields=["full_name"])
        band = band_qilish(self.kitob, self.oquvchi)[0]

        band_qilishni_tasdiqla(band, self.xodim)

        band.refresh_from_db()
        ma_lumot = BandQilishSerializer(band).data
        self.assertEqual(ma_lumot["tasdiqlovchi_fish"], "kutubxonachi")


class BandXabarTest(BandTestBase):
    """Bot «Tasdiqlanganligi xabar qilinadi» deb aytadi — xabar yuborilishi SHART.

    Aks holda yozuv yolg'on bo'ladi: o'quvchi hech qachon natijani bilmaydi.
    """

    def setUp(self):
        super().setUp()
        self.xabarlar = []
        patcher = patch(
            "kitob.services.telegram_xabar_yubor",
            side_effect=lambda chat_id, matn, **kw: self.xabarlar.append((chat_id, matn)),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _commit(self, fn, *args, **kwargs):
        """`transaction.on_commit` ishlasin — `TestCase` har testni tranzaksiya
        ichida yumadi, shuning uchun callback'lar bajarilmay qoladi."""
        with self.captureOnCommitCallbacks(execute=True):
            return fn(*args, **kwargs)

    def test_tasdiqlanganda_oquvchiga_xabar_yuboriladi(self):
        band = band_qilish(self.kitob, self.oquvchi)[0]

        self._commit(band_qilishni_tasdiqla, band, self.xodim)

        self.assertEqual(len(self.xabarlar), 1)
        chat_id, matn = self.xabarlar[0]
        self.assertEqual(chat_id, self.oquvchi.telegram_id)
        self.assertIn("tasdiqlandi", matn.lower())
        self.assertIn(self.kitob.nomi, matn)
        # qaytarish muddati ko'rsatilishi kerak
        self.assertIn("Qaytarish muddati", matn)

    def test_rad_etilganda_oquvchiga_xabar_yuboriladi(self):
        band = band_qilish(self.kitob, self.oquvchi)[0]

        self._commit(band_qilishni_rad_et, band, self.xodim, "Hozircha mavjud emas")

        self.assertEqual(len(self.xabarlar), 1)
        chat_id, matn = self.xabarlar[0]
        self.assertEqual(chat_id, self.oquvchi.telegram_id)
        self.assertIn("rad etildi", matn.lower())
        self.assertIn(self.kitob.nomi, matn)
        # kutubxonachining sababi o'quvchiga yetkazilishi kerak
        self.assertIn("Hozircha mavjud emas", matn)

    def test_xabar_tranzaksiya_rollback_bo_lsa_yuborilmaydi(self):
        """Xabar `on_commit` orqali yuboriladi — rollback bo'lsa yuborilmasin."""
        band = band_qilish(self.kitob, self.oquvchi)[0]

        with self.captureOnCommitCallbacks(execute=True) as bekor_qilingan:
            with self.assertRaises(RuntimeError):
                with transaction.atomic():
                    band_qilishni_tasdiqla(band, self.xodim)
                    raise RuntimeError("rollback")

        self.assertEqual(len(bekor_qilingan), 0)
        self.assertEqual(self.xabarlar, [])
        band.refresh_from_db()
        self.assertEqual(band.holati, "kutmoqda")

    def test_telegram_idsi_yo_q_oquvchiga_xabar_yuborilmaydi(self):
        """Telegram'ga bog'lanmagan o'quvchi uchun yuborish xatosi chiqmasin."""
        self.oquvchi.telegram_id = None
        self.oquvchi.save(update_fields=["telegram_id"])
        band = band_qilish(self.kitob, self.oquvchi)[0]

        self._commit(band_qilishni_tasdiqla, band, self.xodim)

        self.assertEqual(self.xabarlar, [])
        band.refresh_from_db()
        self.assertEqual(band.holati, "tasdiqlandi")

    def test_api_tasdiqlash_xabar_yuboradi(self):
        """Tasdiqlash API orqali kelganda ham xabar yuborilishi kerak."""
        band = band_qilish(self.kitob, self.oquvchi)[0]
        self.kirish()

        javob = self._commit(self.client.post, self.url("holds-approve", band.pk))

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(len(self.xabarlar), 1)
        self.assertEqual(javob.data["holati"], "tasdiqlandi")

    def test_api_rad_etish_xabar_yuboradi(self):
        band = band_qilish(self.kitob, self.oquvchi)[0]
        self.kirish()

        javob = self._commit(
            self.client.post,
            self.url("holds-reject", band.pk),
            {"izoh": "Nusxa yo'q"},
            format="json",
        )

        self.assertEqual(javob.status_code, 200)
        self.assertEqual(len(self.xabarlar), 1)
        self.assertIn("Nusxa yo'q", self.xabarlar[0][1])