"""`Kitob.holati` va `Nusxa.holati` o'zaro bog'lanish testlari.

Muammo: `kitob_ber()` faqat `Nusxa.holati`ni `berilgan`ga o'zgartirardi,
`Kitob.holati` esa butunlay o'zgarishsiz qolardi — kitob ro'yxatida
«Mavjud» deb ko'rinib turar edi. Endi kitob holati nusxalar holatidan
avtomatik hisoblanadi (`kitob.services.kitob_holatini_yenila`).
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from berish.models import Berish
from berish.services import kitob_ber, kitob_ber_by_kitob, kitob_qaytar
from kitob.models import Kitob
from kitob.services import kitob_holatini_yenila
from navbat.models import Navbat
from nusxa.models import Nusxa
from oquvchi.models import Oquvchi

User = get_user_model()


class KitobHolatiTestBase(TestCase):
    def setUp(self):
        super().setUp()
        self.xodim = User.objects.create_user(
            username="kutubxonachi", password="parol12345", full_name="K", rol="kutubxonachi"
        )
        self.kitob = Kitob.objects.create(
            nomi="O'tkan kunlar", muallif="Abdulla Qodiriy", janr="badiiy", nashr_yili=2015
        )
        self.oquvchi = Oquvchi.objects.create(
            fish="Alisher Karimov",
            telefon="+998901234567",
            telegram_id=111111,
            karta_raqami="K-001",
        )

    def nusxa(self, inventar, holati="mavjud"):
        return Nusxa.objects.create(
            kitob=self.kitob,
            inventar_raqami=inventar,
            holati=holati,
            qabul_sana=date(2020, 1, 1),
        )


class KitobHolatiniYenilaTest(KitobHolatiTestBase):
    def test_yangi_kitob_mavjud_holatda(self):
        self.assertEqual(self.kitob.holati, "mavjud")
        self.assertEqual(kitob_holatini_yenila(self.kitob.id), "mavjud")

    def test_mavjud_nusxa_berilganda_kitob_mavjud_qoladi(self):
        """Ko'p nusxali kitobda bittasi berilsa, kitob «Berilgan» bo'lmasligi kerak."""
        self.nusxa("INV-1")
        self.nusxa("INV-2")

        kitob_ber(self.kitob.nusxalar.get(inventar_raqami="INV-1"), self.oquvchi, self.xodim)

        self.kitob.refresh_from_db()
        self.assertEqual(self.kitob.holati, "mavjud")

    def test_oxirgi_nusxa_berilganda_kitob_berilgan_bo_ladi(self):
        """Yakka nusxa berilganda kitob ham «Berilgan» bo'lishi kerak."""
        nusxa = self.nusxa("INV-1")

        kitob_ber(nusxa, self.oquvchi, self.xodim)

        self.kitob.refresh_from_db()
        nusxa.refresh_from_db()
        self.assertEqual(nusxa.holati, "berilgan")
        self.assertEqual(self.kitob.holati, "berilgan")

    def test_berilgan_kitob_qaytarilganda_mavjud_bo_ladi(self):
        nusxa = self.nusxa("INV-1")
        berish = kitob_ber(nusxa, self.oquvchi, self.xodim)
        self.kitob.refresh_from_db()
        self.assertEqual(self.kitob.holati, "berilgan")

        kitob_qaytar(berish, self.xodim)

        self.kitob.refresh_from_db()
        nusxa.refresh_from_db()
        self.assertEqual(nusxa.holati, "mavjud")
        self.assertEqual(self.kitob.holati, "mavjud")

    def test_bitta_nusxa_qaytarilsa_kitob_mavjud_qoladi(self):
        """Ikki nusxa berilgan, bittasi qaytarilgan — kitob «Berilgan» bo'lib qoladi."""
        n1 = self.nusxa("INV-1")
        n2 = self.nusxa("INV-2")
        b1 = kitob_ber(n1, self.oquvchi, self.xodim)
        ikkinchi = Oquvchi.objects.create(
            fish="Shoxista Raximova",
            telefon="+998902345678",
            telegram_id=222222,
            karta_raqami="K-002",
        )
        kitob_ber(n2, ikkinchi, self.xodim)

        self.kitob.refresh_from_db()
        self.assertEqual(self.kitob.holati, "berilgan")

        kitob_qaytar(b1, self.xodim)

        self.kitob.refresh_from_db()
        self.assertEqual(self.kitob.holati, "mavjud")

    def test_yoqolgan_holat_avtomatik_ozgarmaydi(self):
        """«Yo'qolgan» — qo'lda belgilangan doimiy holat, uni tegmaslik kerak."""
        self.nusxa("INV-1")
        self.kitob.holati = "yoqolgan"
        self.kitob.save(update_fields=["holati"])

        nusxa = self.kitob.nusxalar.get(inventar_raqami="INV-1")
        kitob_ber(nusxa, self.oquvchi, self.xodim)

        self.kitob.refresh_from_db()
        self.assertEqual(self.kitob.holati, "yoqolgan")

    def test_nusxasi_yoq_kitob_mavjud_qoladi(self):
        """Nusxa yo'q kitob «Berilgan» bo'lmasligi kerak."""
        self.assertEqual(kitob_holatini_yenila(self.kitob.id), "mavjud")

    def test_berilgan_holat_choices_da_mavjud(self):
        self.assertIn("berilgan", dict(Kitob.HOLAT_CHOICES))


class HolatniTekshirishTest(KitobHolatiTestBase):
    def test_berish_yozuvi_yaratiladi_va_holati_kitobni_belgilaydi(self):
        nusxa = self.nusxa("INV-1")

        berish = kitob_ber(nusxa, self.oquvchi, self.xodim)

        self.assertEqual(Berish.objects.count(), 1)
        self.assertEqual(berish.nusxa_id, nusxa.id)
        self.assertEqual(berish.oquvchi_id, self.oquvchi.id)
        self.assertEqual(berish.holati, "faol")
        self.assertIsNone(berish.qaytarilgan_sana)


class AsliKitobBerishTest(KitobHolatiTestBase):
    """Nusxasi umuman yo'q kitob «asli» holatda beriladi: `Berish.nusxa`
    bo'sh qoladi, kitob esa `Berish.kitob` orqali bog'lanadi."""

    def test_nusxasi_yoq_kitob_asli_beriladi(self):
        berish = kitob_ber_by_kitob(self.kitob, self.oquvchi, self.xodim)

        self.assertIsNone(berish.nusxa_id)
        self.assertEqual(berish.kitob_id, self.kitob.id)
        self.assertEqual(berish.holati, "faol")
        self.assertEqual(berish.bergan_xodim_id, self.xodim.id)

    def test_asli_berilganda_kitob_berilgan_boladi(self):
        kitob_ber_by_kitob(self.kitob, self.oquvchi, self.xodim)

        self.kitob.refresh_from_db()
        self.assertEqual(self.kitob.holati, "berilgan")

    def test_asli_kitob_qaytarilganda_mavjud_bo_ladi(self):
        berish = kitob_ber_by_kitob(self.kitob, self.oquvchi, self.xodim)

        kitob_qaytar(berish, self.xodim)

        self.kitob.refresh_from_db()
        berish.refresh_from_db()
        self.assertEqual(self.kitob.holati, "mavjud")
        self.assertEqual(berish.holati, "qaytarilgan")

    def test_asli_berilgan_kitob_qayta_berilmaydi(self):
        kitob_ber_by_kitob(self.kitob, self.oquvchi, self.xodim)

        ikkinchi = Oquvchi.objects.create(
            fish="Shoxista Raximova",
            telefon="+998902345678",
            telegram_id=222222,
            karta_raqami="K-002",
        )
        with self.assertRaises(ValidationError) as kontekst:
            kitob_ber_by_kitob(self.kitob, ikkinchi, self.xodim)

        self.assertEqual(kontekst.exception.detail["error"], "kitob_band")
        self.assertEqual(Berish.objects.filter(kitob=self.kitob).count(), 1)

    def test_asli_berish_navbatni_yopadi(self):
        navbat = Navbat.objects.create(kitob=self.kitob, oquvchi=self.oquvchi)

        kitob_ber_by_kitob(self.kitob, self.oquvchi, self.xodim)

        navbat.refresh_from_db()
        self.assertEqual(navbat.holati, "yakunlandi")

    def test_nusxa_bo_lsa_asli_berilmaydi(self):
        """Nusxasi bor kitob nusxasiz berilmaydi — xatoga tushadi."""
        self.nusxa("INV-1")

        with self.assertRaises(ValidationError) as kontekst:
            kitob_ber(None, self.oquvchi, self.xodim, kitob=self.kitob)

        self.assertEqual(kontekst.exception.detail["error"], "nusxa_mavjud")


class KitobBoYichaBerishTest(KitobHolatiTestBase):
    """`kitob_ber_by_kitob`: nusxa bor -> nusxa, yo'q -> asli, hammasi band
    -> xato + avtomatik navbat."""

    def test_mavjud_nusxa_avtomatik_beriladi(self):
        nusxa = self.nusxa("INV-1")
        self.nusxa("INV-2")

        berish = kitob_ber_by_kitob(self.kitob, self.oquvchi, self.xodim)

        self.assertEqual(berish.nusxa_id, nusxa.id)
        self.assertIsNotNone(berish.kitob_id)
        nusxa.refresh_from_db()
        self.assertEqual(nusxa.holati, "berilgan")

    def test_barcha_nusxalar_band_bo_lsa_xato_va_avtomatik_navbat(self):
        self.nusxa("INV-1", holati="berilgan")
        self.nusxa("INV-2", holati="berilgan")

        with self.assertRaises(ValidationError) as kontekst:
            kitob_ber_by_kitob(self.kitob, self.oquvchi, self.xodim)

        detail = kontekst.exception.detail
        self.assertEqual(detail["error"], "barcha_nusxalar_berilgan")
        self.assertTrue(detail["navbatga_qoshildi"])
        self.assertEqual(int(detail["orin"]), 1)
        self.assertEqual(Navbat.objects.count(), 1)
        self.assertEqual(Navbat.objects.get().oquvchi_id, self.oquvchi.id)
        self.assertEqual(Berish.objects.count(), 0, "xato bo'lsa kitob berilmasligi kerak")

    def test_bitta_nusxa_bo_sa_ham_qayta_beriladi(self):
        self.nusxa("INV-1", holati="berilgan")
        erkin = self.nusxa("INV-2")

        berish = kitob_ber_by_kitob(self.kitob, self.oquvchi, self.xodim)

        self.assertEqual(berish.nusxa_id, erkin.id)
        self.assertEqual(Navbat.objects.count(), 0)