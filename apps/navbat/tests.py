"""Navbat (queue) tizimi va Telegram taklif xabarlari uchun testlar.

Asosan `services.taklif_yubor` / `keyingi_navbatga_taklif_yubor` orqali
o'tadigan ogohlantirish yo'li tekshiriladi — bu yo'l avval `opuqvchi`
typosi sabab butunlay ishlamay qolgan edi (o'quvchiga xabar yetib
bormasdi, `kitob_qaytar` esa 500 berib, kitob qaytarilganini yana
ko'rsatib qo'yardi).
"""
from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.timezone import now

from berish.models import Berish
from berish.services import kitob_ber, kitob_qaytar
from kitob.models import Kitob
from navbat.models import Navbat
from navbat.services import keyingi_navbatga_taklif_yubor, taklifni_bekor_qil_va_keyingisiga_ut
from navbat.tasks import takliflarni_tekshir
from nusxa.models import Nusxa
from oquvchi.models import Oquvchi

User = get_user_model()

YUBORILGAN = []


def _yubor(chat_id, matn, parse_mode="HTML"):
    YUBORILGAN.append({"chat_id": chat_id, "matn": matn})
    return True


class NavbatTestBase(TestCase):
    def setUp(self):
        super().setUp()
        YUBORILGAN.clear()
        # `from config.telegram import ...` import nomni bog'lab qo'yadi,
        # shuning uchun foydalanuvchi modulini o'zini patch qilamiz.
        # (navbat.tasks bevosita chaqirmaydi — xabar yuborish
        # navbat.services orqali amalga oshadi.)
        for modul in ("navbat.services", "berish.services", "berish.tasks"):
            p = patch(f"{modul}.telegram_xabar_yubor", side_effect=_yubor)
            p.start()
            self.addCleanup(p.stop)

        self.xodim = User.objects.create_user(
            username="kutubxonachi", password="parol12345", full_name="K", rol="kutubxonachi"
        )
        self.kitob = Kitob.objects.create(
            nomi="O'tkan kunlar", muallif="Abdulla Qodiriy", janr="badiiy", nashr_yili=2015
        )
        self.nusxa = Nusxa.objects.create(
            kitob=self.kitob, inventar_raqami="INV-1", holati="mavjud", qabul_sana=date(2020, 1, 1)
        )

    def oquvchi(self, telefon, telegram_id, fish="O'quvchi"):
        return Oquvchi.objects.create(
            fish=fish, telefon=telefon, telegram_id=telegram_id, karta_raqami=f"K-{telefon}"
        )


class TaklifYuborishTest(NavbatTestBase):
    def test_navbatga_tursa_taklif_xabari_yuboriladi(self):
        """Nusxa bo'shashganda navbatdagi birinchi o'quvchiga xabar ketadi."""
        oquvchi = self.oquvchi("+998901234567", 111111)
        Navbat.objects.create(kitob=self.kitob, oquvchi=oquvchi, holati="kutmoqda")

        with self.captureOnCommitCallbacks(execute=True):
            natija = keyingi_navbatga_taklif_yubor(self.nusxa.pk)

        self.assertTrue(natija)
        navbat = Navbat.objects.get()
        self.assertEqual(navbat.holati, "taklif_qilindi")
        self.assertEqual(navbat.ajratilgan_nusxa, self.nusxa)
        self.assertIsNotNone(navbat.taklif_muddati)
        self.nusxa.refresh_from_db()
        self.assertEqual(self.nusxa.holati, "band")

        # Eng muhimi: o'quvchiga Telegram xabari yuborilishi kerak.
        self.assertEqual(len(YUBORILGAN), 1)
        self.assertEqual(YUBORILGAN[0]["chat_id"], 111111)
        self.assertIn("Navbatingiz yaqinlashdi", YUBORILGAN[0]["matn"])
        self.assertIn("O'tkan kunlar", YUBORILGAN[0]["matn"])
        # Xabar yuborilgandan keyin "yuborilgan" bayrog'i tushiriladi —
        # takroriy xabar bo'lmasligi uchun.
        navbat.refresh_from_db()
        self.assertFalse(navbat.taklif_xabari_yuborilgan)

    def test_navbat_bo_sh_bo_lsa_taklif_yuborilmaydi(self):
        with self.captureOnCommitCallbacks(execute=True):
            natija = keyingi_navbatga_taklif_yubor(self.nusxa.pk)
        self.assertFalse(natija)
        self.assertEqual(YUBORILGAN, [])

    def test_nusxa_band_bo_lsa_taklif_yuborilmaydi(self):
        oquvchi = self.oquvchi("+998901234567", 111111)
        Navbat.objects.create(kitob=self.kitob, oquvchi=oquvchi, holati="kutmoqda")
        self.nusxa.holati = "band"
        self.nusxa.save()

        with self.captureOnCommitCallbacks(execute=True):
            natija = keyingi_navbatga_taklif_yubor(self.nusxa.pk)

        self.assertFalse(natija)
        self.assertEqual(YUBORILGAN, [])

    def test_navbat_tartibi_bu_yicha_eng_eski(self):
        """Ikki o'quvchi bo'lsa, eng avval turgan o'quvchiga taklif ketadi."""
        birinchi = self.oquvchi("+998901111111", 111111, "Birinchi")
        ikkinchi = self.oquvchi("+998902222222", 222222, "Ikkinchi")
        Navbat.objects.create(kitob=self.kitob, oquvchi=birinchi, holati="kutmoqda")
        Navbat.objects.create(kitob=self.kitob, oquvchi=ikkinchi, holati="kutmoqda")

        with self.captureOnCommitCallbacks(execute=True):
            keyingi_navbatga_taklif_yubor(self.nusxa.pk)

        self.assertEqual(len(YUBORILGAN), 1)
        self.assertEqual(YUBORILGAN[0]["chat_id"], 111111)
        self.assertEqual(Navbat.objects.get(oquvchi=birinchi).holati, "taklif_qilindi")

    def test_telegramga_ulanmagan_oquvchiga_xabar_yuborilmaydi(self):
        """Xabar yuborib bo'lmasa, bayroq True qoladi (keyin qayta uriniladi)."""
        oquvchi = self.oquvchi("+998901234567", None)
        Navbat.objects.create(kitob=self.kitob, oquvchi=oquvchi, holati="kutmoqda")

        with self.captureOnCommitCallbacks(execute=True):
            keyingi_navbatga_taklif_yubor(self.nusxa.pk)

        self.assertEqual(YUBORILGAN, [])
        navbat = Navbat.objects.get()
        self.assertEqual(navbat.holati, "taklif_qilindi")
        self.assertTrue(navbat.taklif_xabari_yuborilgan)

    def test_xabar_matni_html_escape_qilinadi(self):
        self.kitob.nomi = "<b>Kitob</b> & <script>"
        self.kitob.save()
        oquvchi = self.oquvchi("+998901234567", 111111)
        Navbat.objects.create(kitob=self.kitob, oquvchi=oquvchi, holati="kutmoqda")

        with self.captureOnCommitCallbacks(execute=True):
            keyingi_navbatga_taklif_yubor(self.nusxa.pk)

        matn = YUBORILGAN[0]["matn"]
        self.assertIn("&lt;b&gt;Kitob&lt;/b&gt;", matn)
        self.assertNotIn("<script>", matn)


class KitobQaytarishTest(NavbatTestBase):
    def test_qaytarilganda_navbatga_taklif_yuboriladi(self):
        """Kechiktirib qaytarilgan kitob navbatdagi o'quvchiga taklif etiladi
        va xabar yuboriladi — aks holda navbat to'xtab qolardi."""
        qarz_dor = self.oquvchi("+998901111111", 111111, "Kitob olgan")
        navbatdagi = self.oquvchi("+998902222222", 222222, "Navbatdagi")
        Navbat.objects.create(kitob=self.kitob, oquvchi=navbatdagi, holati="kutmoqda")

        berish = kitob_ber(self.nusxa, qarz_dor, self.xodim)
        with self.captureOnCommitCallbacks(execute=True):
            berish, jarima, taklif_ketdi = kitob_qaytar(berish, self.xodim)

        self.assertTrue(taklif_ketdi)
        self.assertEqual(Navbat.objects.get(oquvchi=navbatdagi).holati, "taklif_qilindi")
        taklif_xabarlari = [x for x in YUBORILGAN if "Navbatingiz" in x["matn"]]
        self.assertEqual(len(taklif_xabarlari), 1)
        self.assertEqual(taklif_xabarlari[0]["chat_id"], 222222)

    def test_navbat_yoq_bo_lsa_qaytarish_muvaffaqiyatli(self):
        """Navbat bo'lmasa ham qaytarish 500 bermasligi kerak (avval shu
        yerda `opuqvchi` typosi xato tushar edi)."""
        oquvchi = self.oquvchi("+998901234567", 111111)
        berish = kitob_ber(self.nusxa, oquvchi, self.xodim)

        with self.captureOnCommitCallbacks(execute=True):
            berish, jarima, taklif_ketdi = kitob_qaytar(berish, self.xodim)

        self.assertFalse(taklif_ketdi)
        berish.refresh_from_db()
        self.assertEqual(berish.holati, "qaytarilgan")
        self.nusxa.refresh_from_db()
        self.assertEqual(self.nusxa.holati, "mavjud")


class TaklifniBekorQilishTest(NavbatTestBase):
    def _muddatni_utkaz(self, navbat):
        """Taklif muddatini o'tgan qilib belgilaymiz."""
        navbat.taklif_muddati = now() - timedelta(minutes=1)
        navbat.save(update_fields=["taklif_muddati"])

    def test_muddat_otgandan_keyin_keyingiga_utadi(self):
        oquvchi = self.oquvchi("+998901234567", 111111, "Birinchi")
        Navbat.objects.create(kitob=self.kitob, oquvchi=oquvchi, holati="kutmoqda")
        with self.captureOnCommitCallbacks(execute=True):
            keyingi_navbatga_taklif_yubor(self.nusxa.pk)
        YUBORILGAN.clear()

        # Birinchi o'quvchi javob bermadi, muddati o'tdi.
        self._muddatni_utkaz(Navbat.objects.get())
        with self.captureOnCommitCallbacks(execute=True):
            takliflarni_tekshir()

        navbat = Navbat.objects.get()
        self.assertEqual(navbat.holati, "bekor")
        self.assertEqual(navbat.bekor_sababi, "muddat_otdi")
        # Navbatda boshqa odam yo'q, shuning uchun yangi taklif xabari
        # yuborilmaydi (lekin nusxa bo'shatilishi kerak).
        self.assertEqual(YUBORILGAN, [])
        self.nusxa.refresh_from_db()
        self.assertEqual(self.nusxa.holati, "mavjud")

    def test_olam_deb_javob_bergan_taklif_bekor_qilinmaydi(self):
        oquvchi = self.oquvchi("+998901234567", 111111)
        Navbat.objects.create(kitob=self.kitob, oquvchi=oquvchi, holati="kutmoqda")
        with self.captureOnCommitCallbacks(execute=True):
            keyingi_navbatga_taklif_yubor(self.nusxa.pk)

        navbat = Navbat.objects.get()
        navbat.javob = "olaman"
        navbat.save(update_fields=["javob"])
        self._muddatni_utkaz(navbat)
        YUBORILGAN.clear()

        with self.captureOnCommitCallbacks(execute=True):
            takliflarni_tekshir()

        navbat.refresh_from_db()
        self.assertEqual(navbat.holati, "taklif_qilindi")

    def test_bir_taklifda_xato_bo_lsa_qolganlari_davom_etadi(self):
        """Bitta taklifni ko'rib chiqishdagi xato boshqalarini to'xtatmasin."""
        for i in range(2):
            # Har biri alohida kitob: bitta kitob uchun faqat bitta
            # "taklif qilindi" navbati mumkin (DB cheklovi).
            kitob = Kitob.objects.create(
                nomi=f"Kitob {i}",
                muallif="Muallif",
                janr="badiiy",
                isbn=f"ISBN-{i}",
                nashr_yili=2015,
            )
            nusxa = Nusxa.objects.create(
                kitob=kitob,
                inventar_raqami=f"INV-T{i}",
                holati="mavjud",
                qabul_sana=date(2020, 1, 1),
            )
            oquvchi = self.oquvchi(f"+9989011111{i:02d}", 111000 + i, f"O'quvchi {i}")
            Navbat.objects.create(kitob=kitob, oquvchi=oquvchi, holati="kutmoqda")
            with self.captureOnCommitCallbacks(execute=True):
                keyingi_navbatga_taklif_yubor(nusxa.pk)

        # Ikkalasining ham muddati o'tadi.
        for navbat in Navbat.objects.filter(holati="taklif_qilindi"):
            self._muddatni_utkaz(navbat)

        with self.captureOnCommitCallbacks(execute=True):
            takliflarni_tekshir()

        self.assertEqual(
            Navbat.objects.filter(holati="bekor").count(), 2, "birinchi xato ikkinchisini to'xtatdi"
        )


class NavbatJavobTest(NavbatTestBase):
    def test_kerak_emas_desak_keyingiga_taklif_ketadi(self):
        birinchi = self.oquvchi("+998901111111", 111111, "Birinchi")
        ikkinchi = self.oquvchi("+998902222222", 222222, "Ikkinchi")
        Navbat.objects.create(kitob=self.kitob, oquvchi=birinchi, holati="kutmoqda")
        Navbat.objects.create(kitob=self.kitob, oquvchi=ikkinchi, holati="kutmoqda")

        with self.captureOnCommitCallbacks(execute=True):
            keyingi_navbatga_taklif_yubor(self.nusxa.pk)
        YUBORILGAN.clear()

        navbat = Navbat.objects.get(oquvchi=birinchi)
        with self.captureOnCommitCallbacks(execute=True):
            taklifni_bekor_qil_va_keyingisiga_ut(navbat, "oquvchi_rad")

        birinchi_navbat = Navbat.objects.get(oquvchi=birinchi)
        self.assertEqual(birinchi_navbat.holati, "bekor")
        self.assertEqual(birinchi_navbat.bekor_sababi, "oquvchi_rad")
        # Ikkinchi o'quvchiga taklif ketishi va xabar borishi kerak.
        self.assertEqual(Navbat.objects.get(oquvchi=ikkinchi).holati, "taklif_qilindi")
        self.assertEqual(len(YUBORILGAN), 1)
        self.assertEqual(YUBORILGAN[0]["chat_id"], 222222)


class BerishEslatmaTest(NavbatTestBase):
    def test_eslatma_vazifasi_xabar_yuboradi(self):
        """Bu vazifa avval `berish.opuqvchi` typosi sabab har doim
        AttributeError bilan yiqilib ketardi."""
        from berish.tasks import eslatma_yuborish

        oquvchi = self.oquvchi("+998901234567", 111111)
        Berish.objects.create(
            nusxa=self.nusxa,
            kitob=self.nusxa.kitob,
            oquvchi=oquvchi,
            bergan_xodim=self.xodim,
            qaytarish_muddati=now().date() + timedelta(days=2),
            holati="faol",
        )

        eslatma_yuborish()

        self.assertEqual(len(YUBORILGAN), 1)
        self.assertEqual(YUBORILGAN[0]["chat_id"], 111111)
        self.assertIn("Qaytarish muddati", YUBORILGAN[0]["matn"])

    def test_takroriy_eslatma_yuborilmaydi(self):
        from berish.tasks import eslatma_yuborish

        oquvchi = self.oquvchi("+998901234567", 111111)
        berish = Berish.objects.create(
            nusxa=self.nusxa,
            kitob=self.nusxa.kitob,
            oquvchi=oquvchi,
            bergan_xodim=self.xodim,
            qaytarish_muddati=now().date() + timedelta(days=2),
            holati="faol",
        )

        eslatma_yuborish()
        YUBORILGAN.clear()
        eslatma_yuborish()

        self.assertEqual(YUBORILGAN, [], "eslatma takroriy yuborildi")
        berish.refresh_from_db()
        self.assertTrue(berish.eslatma_yuborilgan)
