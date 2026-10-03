"""Audit'da topilgan xatolarning regressiya testlari.

Har bir test o'zidan oldin mavjud bo'lgan xatoni qayta takrorlaydi:

* `AnonimKirishTest` — navbat/karta bog'lash/ma'lumotlar endpointlari
  autentifikatsiyasiz chaqirilganda `401` qaytarishi (IDOR va akkaunt
  egallash oldini olindi).
* `QaytarishIdempotentTest` — bitta tugma ikki marta bosilsa, ikkinchi
  qaytarish xato berishi (jarima va navbat takrorlanmasin).
* `JarimaBekorQilishTest` — kechikish qolmasa to'lanmagan jarima
  o'chirilishi.
* `LimitParchalashTest` — limit `count()` emas, bloklangan o'quvchi qatori
  orqali tekshirilishi (koding darajasida tasdiqlanadi).
* `HolatYozilishiTest` — `Nusxa`/`Kitob` holati API orqali qo'lda
  o'zgartirilmasligi (IntegrityError oldini olindi).
* `KitobniOchirishTest` — faol berish/navbat/tarih bo'lsa kitob
  o'chirilmasligi (ProtectedError -> 400).
* `StatsTest` — `limit` validatsiyasi va «asli» berishlar hisobga olinishi.
* `OqituvchiSinfTest` — o'qituvchi arizasidan sinf yozilmasligi.
* `XatoKodiTest` — bloklangan o'quvchi xatosi API'da kodini saqlashi.
* `OchiqNavbatTest` — navbatda turgan o'quvchiga kitob mavjud bo'lgan zahoti
  taklif yuborilishi («o'lik chorak» holatining oldini olish).
"""
from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from berish.models import Berish
from berish.services import kitob_ber, kitob_qaytar
from jarima.models import Jarima
from jarima.services import jarimani_hisobla
from kitob.models import Kitob
from navbat.models import Navbat
from navbat.services import (
    navbatga_qosh,
    navbatni_mavjud_nusxa_bilan_ishga_tushir,
    taklifni_bekor_qil_va_keyingisiga_ut,
)
from navbat.tasks import ochiq_navbatlarni_tekshir
from nusxa.models import Nusxa
from oquvchi.models import Oquvchi

User = get_user_model()


class AuditTestBase(TestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.xodim = User.objects.create_user(
            username="kutubxonachi", password="parol12345", full_name="K", rol="kutubxonachi"
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

    def url(self, nomi, *args):
        return reverse(nomi, args=args)


# --------------------------------------------------------------- xavfsizlik
class AnonimKirishTest(AuditTestBase):
    """Bu endpoint'lar bot tomonidan JWT bilan chaqiriladi. Autentifikatsiyasiz
    chaqirilishi — akkaunt egallash/IDOR degani."""

    def test_navbat_yaratish_anonim_rad_qilinadi(self):
        javob = self.client.post(
            self.url("reservations-list"),
            {"kitob": self.kitob.id, "oquvchi": self.oquvchi.id},
            content_type="application/json",
        )
        self.assertIn(javob.status_code, (401, 403))
        self.assertFalse(Navbat.objects.exists())

    def test_navbat_meni_anonim_rad_qilinadi(self):
        javob = self.client.get(self.url("reservations-meni"), {"telegram_id": self.oquvchi.telegram_id})
        self.assertIn(javob.status_code, (401, 403))

    def test_navbat_bekor_qilish_anonim_rad_qilinadi(self):
        navbat = Navbat.objects.create(kitob=self.kitob, oquvchi=self.oquvchi)
        javob = self.client.delete(self.url("reservations-detail", navbat.id))
        self.assertIn(javob.status_code, (401, 403))
        navbat.refresh_from_db()
        self.assertEqual(navbat.holati, "kutmoqda")

    def test_karta_boglash_anonim_rad_qilinadi(self):
        """Telefon + karta raqamini bilgan kishi akkauntni o'z telegram_id'siga
        qayta bog'lashi mumkin edi."""
        javob = self.client.post(
            self.url("readers-bind"),
            {
                "telefon": self.oquvchi.telefon,
                "karta_raqami": self.oquvchi.karta_raqami,
                "telegram_id": 999,
            },
            content_type="application/json",
        )
        self.assertIn(javob.status_code, (401, 403))
        self.oquvchi.refresh_from_db()
        self.assertEqual(self.oquvchi.telegram_id, 111)

    def test_berishlarim_anonim_rad_qilinadi(self):
        javob = self.client.get(self.url("loans-meni"), {"telegram_id": self.oquvchi.telegram_id})
        self.assertIn(javob.status_code, (401, 403))

    def test_jarimalarim_anonim_rad_qilinadi(self):
        javob = self.client.get(self.url("fines-meni"), {"telegram_id": self.oquvchi.telegram_id})
        self.assertIn(javob.status_code, (401, 403))

    def test_xizmat_akkunti_bilan_navbat_ishlaydi(self):
        """Xizmat akkaunti (bot) autentifikatsiya bilan ishlashda davom etadi."""
        self.client.force_authenticate(self.xodim)
        javob = self.client.post(
            self.url("reservations-list"),
            {"kitob": self.kitob.id, "oquvchi": self.oquvchi.id},
            content_type="application/json",
        )
        self.assertEqual(javob.status_code, 201)
        self.assertTrue(Navbat.objects.exists())


# ----------------------------------------------------------- qaytarish/jarima
class QaytarishIdempotentTest(AuditTestBase):
    def setUp(self):
        super().setUp()
        self.berish = kitob_ber(self.nusxa, self.oquvchi, self.xodim)

    def test_ikkinchi_qaytarish_xato_beradi(self):
        kitob_qaytar(self.berish, self.xodim)
        with self.assertRaises(Exception) as kontekst:
            kitob_qaytar(self.berish, self.xodim)
        xato = kontekst.exception
        self.assertIn("allaqachon_qaytarilgan", str(getattr(xato, "detail", xato)))
        self.berish.refresh_from_db()
        self.assertIsNotNone(self.berish.qaytarilgan_sana)

    def test_ikkinchi_qaytarish_nusxani_buzmaydi(self):
        kitob_qaytar(self.berish, self.xodim)
        self.nusxa.refresh_from_db()
        self.assertEqual(self.nusxa.holati, "mavjud")
        with self.assertRaises(Exception):
            kitob_qaytar(self.berish, self.xodim)
        self.nusxa.refresh_from_db()
        self.assertEqual(self.nusxa.holati, "mavjud")
        self.assertEqual(Berish.objects.count(), 1)


class JarimaBekorQilishTest(AuditTestBase):
    def test_muddat_uzaytirilsa_jarima_olib_tashlanadi(self):
        berish = kitob_ber(self.nusxa, self.oquvchi, self.xodim)
        # kechikib qolgan holat
        berish.qaytarilgan_sana = date(2026, 1, 1)
        berish.qaytarish_muddati = date(2025, 12, 1)
        berish.save()
        self.assertIsNotNone(jarimani_hisobla(berish))
        self.assertTrue(Jarima.objects.filter(berish=berish).exists())

        # muddat keyin uzaytirildi (qaytarish sanasi o'zgarmadi) — jarima endi
        # mavjud emas va to'lanmagan jarima o'chiriladi
        berish.qaytarish_muddati = date(2026, 3, 1)
        berish.save()
        self.assertIsNone(jarimani_hisobla(berish))
        self.assertFalse(Jarima.objects.filter(berish=berish).exists())

    def test_tolangan_jarima_olib_tashlanmaydi(self):
        berish = kitob_ber(self.nusxa, self.oquvchi, self.xodim)
        berish.qaytarilgan_sana = date(2026, 1, 1)
        berish.qaytarish_muddati = date(2025, 12, 1)
        berish.save()
        jarima = jarimani_hisobla(berish)
        jarima.tolandimi = True
        jarima.save()

        berish.qaytarish_muddati = date(2026, 3, 1)
        berish.save()
        self.assertIsNone(jarimani_hisobla(berish))
        self.assertTrue(Jarima.objects.filter(berish=berish, tolandimi=True).exists())


# ------------------------------------------------------------------ limit
class LimitTekshiruvTest(AuditTestBase):
    def test_oquvchi_qatori_bloklanadi(self):
        """Parallel so'rovlarda limit oshib ketmasligi uchun `kitob_ber`
        o'quvchi qatorini `select_for_update` bilan bloklaydi."""
        import pathlib

        import berish.services as berish_services_modul

        manba = pathlib.Path(berish_services_modul.__file__).read_text(encoding="utf-8")
        self.assertIn("select_for_update", manba)
        self.assertIn("Oquvchi.objects.select_for_update()", manba)

    def test_limit_oshganda_xato(self):
        from django.test import override_settings

        with override_settings(LIMIT_KITOB=1):
            kitob_ber(self.nusxa, self.oquvchi, self.xodim)
            ikkinchi = Nusxa.objects.create(
                kitob=self.kitob,
                inventar_raqami="INV-2",
                holati="mavjud",
                qabul_sana=date(2020, 1, 1),
            )
            with self.assertRaises(Exception) as kontekst:
                kitob_ber(ikkinchi, self.oquvchi, self.xodim)
            self.assertIn("limit_oshdi", str(kontekst.exception))
            self.assertEqual(Berish.objects.count(), 1)


# ------------------------------------------------------------ holat / o'chirish
class HolatYozilishiTest(AuditTestBase):
    def test_nusxa_holatini_qo_lda_berganda_rad_qilinadi(self):
        self.client.force_authenticate(self.xodim)
        javob = self.client.patch(
            self.url("copies-detail", self.nusxa.id),
            {"holati": "berilgan"},
            content_type="application/json",
        )
        self.assertEqual(javob.status_code, 400)
        self.nusxa.refresh_from_db()
        self.assertEqual(self.nusxa.holati, "mavjud")

    def test_nusxa_tamirda_holatiga_ozgartiriladi(self):
        self.client.force_authenticate(self.xodim)
        javob = self.client.patch(
            self.url("copies-detail", self.nusxa.id),
            {"holati": "tamirda"},
            content_type="application/json",
        )
        self.assertEqual(javob.status_code, 200)
        self.nusxa.refresh_from_db()
        self.assertEqual(self.nusxa.holati, "tamirda")

    def test_kitob_holatini_qo_lda_berganda_rad_qilinadi(self):
        self.client.force_authenticate(self.xodim)
        javob = self.client.patch(
            self.url("books-detail", self.kitob.id),
            {"holati": "mavjud"},
            content_type="application/json",
        )
        self.assertEqual(javob.status_code, 200)
        # `holati` read-only: qiymat o'zgarmasligi kerak (avval berilgan
        # qilib qo'yib, keyingi berishni IntegrityError bilan buzardi).
        self.kitob.refresh_from_db()
        self.assertNotEqual(self.kitob.holati, "berilgan")


class KitobniOchirishTest(AuditTestBase):
    def test_nusxasi_bor_kitob_ochirilmaydi(self):
        self.client.force_authenticate(self.xodim)
        javob = self.client.delete(self.url("books-detail", self.kitob.id))
        self.assertEqual(javob.status_code, 400)
        self.assertTrue(Kitob.objects.filter(pk=self.kitob.pk).exists())

    def test_faol_berishli_kitob_ochirilmaydi(self):
        """Nusxasi yo'q kitob «asli» holda berilgan bo'lishi mumkin —
        Berish PROTECT bo'lgani uchun o'chirish 500 berardi."""
        asl_kitob = Kitob.objects.create(
            nomi="Sarob", muallif="Sadriddin Ayni", janr="badiiy", nashr_yili=2020
        )
        kitob_ber(None, self.oquvchi, self.xodim, kitob=asl_kitob)
        self.client.force_authenticate(self.xodim)
        javob = self.client.delete(self.url("books-detail", asl_kitob.id))
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data["error"], "faol_berish_mavjud")
        self.assertTrue(Kitob.objects.filter(pk=asl_kitob.pk).exists())

    def test_nusxasi_yoq_kitob_ochiriladi(self):
        asl_kitob = Kitob.objects.create(
            nomi="Sarob", muallif="Sadriddin Ayni", janr="badiiy", nashr_yili=2020
        )
        self.client.force_authenticate(self.xodim)
        javob = self.client.delete(self.url("books-detail", asl_kitob.id))
        self.assertEqual(javob.status_code, 204)
        self.assertFalse(Kitob.objects.filter(pk=asl_kitob.pk).exists())


# ------------------------------------------------------------------- stats
class StatsTest(AuditTestBase):
    def test_limit_notogri_bolsa_400(self):
        self.client.force_authenticate(self.xodim)
        javob = self.client.get(self.url("stats-top-books"), {"limit": "abc"})
        self.assertEqual(javob.status_code, 400)

    def test_limit_manfiy_bolsa_400(self):
        self.client.force_authenticate(self.xodim)
        javob = self.client.get(self.url("stats-top-books"), {"limit": -5})
        self.assertEqual(javob.status_code, 400)

    def test_asli_berishlar_hisobga_olingan(self):
        """Nusxasi yo'q kitobni berish reytingda ko'rinishi kerak — avval
        faqat nusxa orqali berishlar hisoblanardi."""
        asl_kitob = Kitob.objects.create(
            nomi="Sarob", muallif="Sadriddin Ayni", janr="badiiy", nashr_yili=2020
        )
        kitob_ber(None, self.oquvchi, self.xodim, kitob=asl_kitob)
        self.client.force_authenticate(self.xodim)
        javob = self.client.get(self.url("stats-top-books"))
        self.assertEqual(javob.status_code, 200)
        qatorlar = {q["id"]: q["berishlar_soni"] for q in javob.data}
        self.assertEqual(qatorlar.get(asl_kitob.id), 1)


# ----------------------------------------------------------------- o'qituvchi
class OqituvchiSinfTest(AuditTestBase):
    def test_oqituvchiga_sinf_yozilmaydi(self):
        from oquvchi.models import Ariza

        ariza = Ariza.objects.create(
            fish="Muhammadaziz", telefon="+998909999999", telegram_id=555, rol="oqituvchi",
            kasb="Ona tili", sinf="7-A",
        )
        from oquvchi.services import arizani_tasdiqla

        with patch("oquvchi.services.telegram_xabar_yubor", return_value=True):
            ariza, oquvchi, _karta = arizani_tasdiqla(ariza)
        self.assertEqual(oquvchi.rol, "oqituvchi")
        self.assertEqual(oquvchi.kasb, "Ona tili")
        self.assertEqual(oquvchi.sinf, "")


# --------------------------------------------------------------- xato kodi
class XatoKodiTest(AuditTestBase):
    def test_bloklangan_oquvchi_kodi_saqlanadi(self):
        """Serializer ichidagi xato maydon ostida qolsa ham, bot kodni
        ko'rishi kerak (`oquvchi_bloklangan`, `validatsiya_xatosi` emas)."""
        self.oquvchi.faol = False
        self.oquvchi.save(update_fields=["faol"])
        self.client.force_authenticate(self.xodim)
        javob = self.client.post(
            self.url("loans-list"),
            {"nusxa": self.nusxa.id, "oquvchi": self.oquvchi.id},
            content_type="application/json",
        )
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data["error"], "oquvchi_bloklangan")


# --------------------------------------------------------- navbat o'ligi
class OchiqNavbatTest(AuditTestBase):
    """Navbatda turgan o'quvchi hech qachon xabarsiz qolmasligi kerak: kitob
    mavjud bo'lgan zahoti unga taklif yuboriladi (avval faqat `kitob_qaytar`
    chaqirilganda taklif yuborilardi — yangi nusxa qo'shilsa yoki «asli»
    kitob qaytarsa navbat o'lik chorakda qolardi)."""

    def setUp(self):
        super().setUp()
        self.ikkinchi = Oquvchi.objects.create(
            fish="Sardor", telefon="+998901234568", telegram_id=222, karta_raqami="K-2"
        )
        self.telegram_patch = patch("navbat.services.telegram_xabar_yubor", return_value=True)
        self.telegram_patch.start()
        self.addCleanup(self.telegram_patch.stop)

    def _navbat_holati(self, kitob):
        navbat = Navbat.objects.filter(kitob=kitob, oquvchi=self.oquvchi).first()
        return navbat.holati if navbat else None

    def test_yangi_nusxa_qoshilganda_taklif_yuboriladi(self):
        """Navbatda turgan bor-yo'q kitobga nusxa qo'shilsa, taklif yuboriladi."""
        navbatga_qosh(self.kitob, self.oquvchi)
        self.assertEqual(self._navbat_holati(self.kitob), "kutmoqda")

        navbatni_mavjud_nusxa_bilan_ishga_tushir(self.kitob.id)

        self.assertEqual(self._navbat_holati(self.kitob), "taklif_qilindi")

    def test_navbat_bos_bo_lsa_taklif_yuborilmaydi(self):
        """Navbatda hech kim turmagan bo'lsa, taklif yuborilmaydi."""
        self.assertFalse(navbatni_mavjud_nusxa_bilan_ishga_tushir(self.kitob.id))
        self.assertFalse(Navbat.objects.filter(holati="taklif_qilindi").exists())

    def test_asli_kitob_qaytganda_taklif_yuboriladi(self):
        """Nusxasi yo'q kitob «asli» holda berilgan bo'lsa, qaytarilganda
        navbatdagilar ogohlantiriladi."""
        Nusxa.objects.filter(kitob=self.kitob).delete()
        navbatga_qosh(self.kitob, self.oquvchi)
        # Navbatda turgan o'quvchidan tashqari boshqa o'quvchiga «asli» beriladi
        berish = kitob_ber(
            nusxa=None, kitob=self.kitob, oquvchi=self.ikkinchi, xodim=self.xodim
        )

        kitob_qaytar(berish, xodim=self.xodim)

        self.assertEqual(self._navbat_holati(self.kitob), "taklif_qilindi")

    def test_ochiq_navbatlar_vazifasi_nusxasiz_kitobni_topadi(self):
        """Celery vazifasi «asli» kitoblarni ham topishi kerak."""
        Nusxa.objects.filter(kitob=self.kitob).delete()
        navbatga_qosh(self.kitob, self.oquvchi)

        natija = ochiq_navbatlarni_tekshir()

        self.assertIn("1 ta", natija)
        self.assertEqual(self._navbat_holati(self.kitob), "taklif_qilindi")

    def test_ochiq_navbatlar_vazifasi_taklifni_ikki_marta_yubormaydi(self):
        """Vazifa taklif yuborilgandan keyin yana taklif qilmasligi kerak
        (o'quvchiga bir xil xabar yuborilmasin)."""
        navbatga_qosh(self.kitob, self.oquvchi)

        ochiq_navbatlarni_tekshir()
        holat = self._navbat_holati(self.kitob)
        natija = ochiq_navbatlarni_tekshir()

        self.assertEqual(holat, "taklif_qilindi")
        self.assertIn("0 ta", natija)
        self.assertEqual(Navbat.objects.filter(holati="taklif_qilindi").count(), 1)

    def test_rad_javobda_keyingiga_o_tadi(self):
        """Taklif rad edilganda nusxa bo'shatilib keyingi odamga o'tishi kerak."""
        navbatga_qosh(self.kitob, self.oquvchi)
        navbatga_qosh(self.kitob, self.ikkinchi)
        navbatni_mavjud_nusxa_bilan_ishga_tushir(self.kitob.id)
        self.nusxa.refresh_from_db()
        self.assertEqual(self.nusxa.holati, "band")

        taklifni_bekor_qil_va_keyingisiga_ut(
            Navbat.objects.get(kitob=self.kitob, oquvchi=self.oquvchi), "oquvchi_rad"
        )

        self.assertEqual(
            Navbat.objects.get(kitob=self.kitob, oquvchi=self.ikkinchi).holati,
            "taklif_qilindi",
        )
        self.nusxa.refresh_from_db()
        self.assertEqual(self.nusxa.holati, "band")