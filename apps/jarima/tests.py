"""Jarima hisoblash va Telegram eslatma vazifalari uchun testlar.

Asosan `jarima_eslatma_yubor` tekshiriladi — bu vazifa avval
`jarima.berish.opuqvchi` typosi sabab birinchi qatorda
AttributeError tushib, hech qanday o'quvchiga eslatma yubora
olmasdi. Takroriy xabar bo'lmasligi ham alohida tekshiriladi.
"""
from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils.timezone import now

from berish.models import Berish
from jarima.models import Jarima
from jarima.services import jarimani_hisobla
from jarima.tasks import jarima_eslatma_yubor, jarimalarni_hisobla
from kitob.models import Kitob
from nusxa.models import Nusxa
from oquvchi.models import Oquvchi

User = get_user_model()

YUBORILGAN = []


def _yubor(chat_id, matn, parse_mode="HTML"):
    YUBORILGAN.append({"chat_id": chat_id, "matn": matn})
    return True


class JarimaTestBase(TestCase):
    def setUp(self):
        super().setUp()
        YUBORILGAN.clear()
        # `from config.telegram import ...` import nomni bog'lab qo'yadi,
        # shuning uchun foydalanuvchi modullarini o'zlarini patch qilamiz.
        for modul in ("jarima.tasks", "jarima.views", "berish.services"):
            p = patch(f"{modul}.telegram_xabar_yubor", side_effect=_yubor)
            p.start()
            self.addCleanup(p.stop)

        self.xodim = User.objects.create_user(
            username="kutubxonachi", password="parol12345", full_name="K", rol="kutubxonachi"
        )
        self.kitob = Kitob.objects.create(
            nomi="Navoiy", muallif="Alisher Navoiy", janr="badiiy", nashr_yili=2010
        )
        self.nusxa = Nusxa.objects.create(
            kitob=self.kitob, inventar_raqami="INV-1", holati="berilgan", qabul_sana=date(2020, 1, 1)
        )

    def kechikkan_berish(self, oquvchi, kunlar=3, tasdiq=False):
        berish = Berish.objects.create(
            nusxa=self.nusxa,
            oquvchi=oquvchi,
            bergan_xodim=self.xodim,
            berilgan_sana=date(2020, 1, 1),
            qaytarish_muddati=date.today() - timedelta(days=kunlar),
            qaytarilgan_sana=date.today() - timedelta(days=1) if tasdiq else None,
            holati="qaytarilgan" if tasdiq else "faol",
        )
        if tasdiq:
            jarimani_hisobla(berish)
        return berish


class JarimaHisoblashTest(JarimaTestBase):
    def test_muddat_otganda_jarima_yuzaga_keladi(self):
        oquvchi = Oquvchi.objects.create(
            fish="A", telefon="+998901234567", telegram_id=111111, karta_raqami="K1"
        )
        # Hali qaytarilmagan berish: kechikish bugungi kundan hisoblanadi.
        berish = self.kechikkan_berish(oquvchi, kunlar=3)
        jarima = jarimani_hisobla(berish)
        self.assertIsNotNone(jarima)
        self.assertEqual(jarima.kechikkan_kunlar, 3)

    def test_vaqtida_qaytarilgan_berishga_jarima_yoq(self):
        oquvchi = Oquvchi.objects.create(
            fish="A", telefon="+998901234567", telegram_id=111111, karta_raqami="K1"
        )
        berish = self.kechikkan_berish(oquvchi, kunlar=3)
        berish.qaytarilgan_sana = berish.qaytarish_muddati - timedelta(days=5)
        berish.save()
        self.assertIsNone(jarimani_hisobla(berish))

    def test_jarima_takrorlanmaydi(self):
        oquvchi = Oquvchi.objects.create(
            fish="A", telefon="+998901234567", telegram_id=111111, karta_raqami="K1"
        )
        berish = self.kechikkan_berish(oquvchi, kunlar=3)
        jarimani_hisobla(berish)
        jarimani_hisobla(berish)
        self.assertEqual(Jarima.objects.filter(berish=berish).count(), 1)

    def test_tolangan_jarima_qayta_hisoblanmaydi(self):
        oquvchi = Oquvchi.objects.create(
            fish="A", telefon="+998901234567", telegram_id=111111, karta_raqami="K1"
        )
        berish = self.kechikkan_berish(oquvchi, kunlar=3)
        jarima = jarimani_hisobla(berish)
        jarima.tolandimi = True
        jarima.summa = Decimal("100")
        jarima.save()

        qayta = jarimani_hisobla(berish)
        self.assertEqual(qayta.summa, Decimal("100"), "to'langan jarima ustidan yozildi")

    def test_kunlik_vazifa_tolanmaganlarni_hisoblaydi(self):
        oquvchi = Oquvchi.objects.create(
            fish="A", telefon="+998901234567", telegram_id=111111, karta_raqami="K1"
        )
        self.kechikkan_berish(oquvchi, kunlar=3)
        jarimalarni_hisobla()
        self.assertEqual(Jarima.objects.count(), 1)


class JarimaEslatmaTest(JarimaTestBase):
    """Asosiy tekshiruv: eslatma vazifasi xabar yuborishi SHART."""

    def oquvchi(self, telefon, telegram_id, fish="A"):
        return Oquvchi.objects.create(
            fish=fish, telefon=telefon, telegram_id=telegram_id, karta_raqami=f"K-{telefon}"
        )

    def test_eslatma_xabari_yuboriladi(self):
        oquvchi = self.oquvchi("+998901234567", 111111)
        self.kechikkan_berish(oquvchi, kunlar=3, tasdiq=True)

        jarima_eslatma_yubor()

        self.assertEqual(len(YUBORILGAN), 1, "eslatma yuborilmadi")
        self.assertEqual(YUBORILGAN[0]["chat_id"], 111111)
        self.assertIn("Jarima eslatmasi", YUBORILGAN[0]["matn"])
        self.assertIn("Navoiy", YUBORILGAN[0]["matn"])
        self.assertIn("qarz", YUBORILGAN[0]["matn"])

    def test_takroriy_eslatma_24_soat_ichida_yuborilmaydi(self):
        oquvchi = self.oquvchi("+998901234567", 111111)
        self.kechikkan_berish(oquvchi, kunlar=3, tasdiq=True)

        jarima_eslatma_yubor()
        self.assertEqual(len(YUBORILGAN), 1)
        YUBORILGAN.clear()

        # 3 soatlik intervalda qayta chaqirilsa ham yuborilmasligi kerak.
        jarima_eslatma_yubor()
        self.assertEqual(YUBORILGAN, [], "takroriy xabar yuborildi")

    def test_takror_muddat_utgach_qayta_yuboriladi(self):
        oquvchi = self.oquvchi("+998901234567", 111111)
        berish = self.kechikkan_berish(oquvchi, kunlar=3, tasdiq=True)

        jarima_eslatma_yubor()
        Jarima.objects.update(eslatma_yuborilgan_sana=now() - timedelta(days=2))
        YUBORILGAN.clear()

        jarima_eslatma_yubor()
        self.assertEqual(len(YUBORILGAN), 1, "muddat o'tsa ham yuborilmadi")

    def test_tolangan_qarzga_eslatma_yuborilmaydi(self):
        oquvchi = self.oquvchi("+998901234567", 111111)
        berish = self.kechikkan_berish(oquvchi, kunlar=3, tasdiq=True)
        Jarima.objects.filter(berish=berish).update(tolandimi=True)

        jarima_eslatma_yubor()
        self.assertEqual(YUBORILGAN, [])

    def test_telegramga_ulanmagan_oquvchiga_eslatma_yuborilmaydi(self):
        oquvchi = self.oquvchi("+998901234567", None)
        self.kechikkan_berish(oquvchi, kunlar=3, tasdiq=True)

        jarima_eslatma_yubor()
        self.assertEqual(YUBORILGAN, [])

    def test_bir_oquvchining_barcha_qarzi_bitta_xabarda(self):
        """Ikki kitob qarzdor bo'lsa, o'quvchiga bitta xabar ketadi."""
        oquvchi = self.oquvchi("+998901234567", 111111)
        self.kechikkan_berish(oquvchi, kunlar=3, tasdiq=True)
        ikkinchi_nusxa = Nusxa.objects.create(
            kitob=self.kitob, inventar_raqami="INV-2", holati="berilgan", qabul_sana=date(2020, 1, 1)
        )
        berish2 = Berish.objects.create(
            nusxa=ikkinchi_nusxa,
            oquvchi=oquvchi,
            bergan_xodim=self.xodim,
            berilgan_sana=date(2020, 1, 1),
            qaytarish_muddati=date.today() - timedelta(days=5),
            qaytarilgan_sana=date.today() - timedelta(days=2),
            holati="qaytarilgan",
        )
        jarimani_hisobla(berish2)

        jarima_eslatma_yubor()

        self.assertEqual(len(YUBORILGAN), 1, "o'quvchiga bittadan ko'p xabar yuborildi")
        self.assertEqual(Jarima.objects.filter(berish__oquvchi=oquvchi, tolandimi=False).count(), 2)

    def test_bir_jarimasi_yaqinda_eslatilgan_bo_lsa_boshqasi_ham_yuborilmaydi(self):
        """Bitta jarima yaqinda eslatilgan bo'lsa, o'sha o'quvchining boshqa
        jarimalari ham ushbu chaqiruvda yuborilmasligi kerak (qisman xabar
        yuborilmasin)."""
        oquvchi = self.oquvchi("+998901234567", 111111)
        berish = self.kechikkan_berish(oquvchi, kunlar=3, tasdiq=True)
        Jarima.objects.filter(berish=berish).update(eslatma_yuborilgan_sana=now())

        jarima_eslatma_yubor()
        self.assertEqual(YUBORILGAN, [])

    def test_xabar_matnida_html_escape_qilinadi(self):
        self.kitob.nomi = "<b>Kitob</b> & <script>"
        self.kitob.save()
        self.nusxa.save()
        oquvchi = self.oquvchi("+998901234567", 111111)
        self.kechikkan_berish(oquvchi, kunlar=3, tasdiq=True)

        jarima_eslatma_yubor()

        matn = YUBORILGAN[0]["matn"]
        self.assertIn("&lt;b&gt;Kitob&lt;/b&gt;", matn)
        self.assertNotIn("<script>", matn)


class TozalashJarimalarTest(JarimaTestBase):
    """`tozalash_jarimalar` command'i: o'quvchi yo'q / nofaol o'quvchilarning
    to'lanmagan jarimalarini tozalaydi."""

    def oquvchi(self, telefon, telegram_id, faol=True):
        return Oquvchi.objects.create(
            fish="A", telefon=telefon, telegram_id=telegram_id, faol=faol,
            karta_raqami=f"K-{telefon}",
        )

    def ishga_tushir(self, *args):
        out = StringIO()
        call_command("tozalash_jarimalar", *args, stdout=out, stderr=out)
        return out.getvalue()

    def test_odatdagi_holatda_hech_narsa_topilmaydi(self):
        oquvchi = self.oquvchi("+998901234567", 111111)
        self.kechikkan_berish(oquvchi, tasdiq=True)
        chiqish = self.ishga_tushir()
        self.assertIn("topilmadi", chiqish)
        self.assertEqual(Jarima.objects.count(), 1)

    def test_nofaol_oquvchining_jarimasi_ko_rsatiladi_va_ochiriladi(self):
        faol = self.oquvchi("+998901234567", 111111)
        nofaol = self.oquvchi("+998901234568", 222222, faol=False)
        self.kechikkan_berish(faol, tasdiq=True)
        self.kechikkan_berish(nofaol, tasdiq=True)
        self.assertEqual(Jarima.objects.count(), 2)

        # Sukut bo'yicha faqat ko'rsatadi, o'chirmaydi.
        chiqish = self.ishga_tushir()
        self.assertIn("nofaol", chiqish)
        self.assertIn("--o'chirish", chiqish)
        self.assertEqual(Jarima.objects.count(), 2, "ko'rsatish o'chirishga aylantirilib ketdi")

        # Aniq buyruq bilan o'chadi.
        self.ishga_tushir("--o'chirish")
        self.assertEqual(Jarima.objects.count(), 1, "nofaol o'quvchining jarimasi o'chirilmadi")
        self.assertFalse(Jarima.objects.filter(berish__oquvchi=nofaol).exists())

    def test_tolangan_jarima_hech_qachon_ochirilmaydi(self):
        """To'langan jarima — moliyaviy tarix, uni o'chirish mumkin emas."""
        oquvchi = self.oquvchi("+998901234567", 111111, faol=False)
        berish = self.kechikkan_berish(oquvchi, tasdiq=True)
        Jarima.objects.filter(berish=berish).update(tolandimi=True)

        self.ishga_tushir("--o'chirish")
        self.assertEqual(Jarima.objects.count(), 1, "to'langan jarima o'chirildi!")

    def test_faqat_nofaol_filtri_borish_yoqini_aytadi(self):
        self.ishga_tushir("--faqat-nofaol")
        self.assertEqual(Jarima.objects.count(), 0)
