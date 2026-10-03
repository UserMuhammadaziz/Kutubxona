"""O'quvchi va a'zolik arizalari moduli uchun testlar.

Asosan ariza (membership application) oqimi tekshiriladi: bot orqali yuborish,
holatni ko'rish, kutubxonachi tomondan qabul/rad etish va shu jarayonda
Telegram xabarining yuborilishi. Telegram so'rovlari tarmoqqa chiqmasligi
uchun `telegram_xabar_yubor` mock qilinadi.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.timezone import now
from rest_framework.test import APIClient

from .models import Ariza, Oquvchi

User = get_user_model()

YUBORILGAN_XABARLAR = []


def _xabar_yuborilgan(chat_id, matn, parse_mode="HTML"):
    YUBORILGAN_XABARLAR.append({"chat_id": chat_id, "matn": matn})
    return True


class ArizaTestMixin:
    def setUp(self):
        super().setUp()
        YUBORILGAN_XABARLAR.clear()
        # Muhim: `from config.telegram import telegram_xabar_yubor` ko'rinishidagi
        # import nomni import vaqtida bog'laydi, shuning uchun `config.telegram`
        # ni mock qilish o'quvchi moduli ichidagi haqiqiy chaqiruvga ta'sir
        # qilmaydi. Foydalanuvchi modulining o'zini patch qilamiz.
        self.patcher = patch(
            "oquvchi.services.telegram_xabar_yubor", side_effect=_xabar_yuborilgan
        )
        self.yuborish = self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.xodim = User.objects.create_user(
            username="kutubxonachi",
            password="parol12345",
            full_name="Kutubxonachi",
            rol="kutubxonachi",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.xodim)

    def xabarni_tekshir(self):
        """on_commit kalitlarini bajarib, yuborilgan xabarlarni ro'yxatga oladi.

        `ariza_holatini_yubor` xabarni `transaction.on_commit` orqali yuboradi
        (bekor qilingan tranzaksiyadan keyin xabar ketmasligi uchun).
        `TestCase` har testni tranzaksiya ichida yumib, on_commit
        qaychalovlarini bajar maydi — shuning uchun ularni qo'lda
        `captureOnCommitCallbacks(execute=True)` orqali ishga tushiramiz.
        """
        return self.captureOnCommitCallbacks(execute=True)


class ArizaYuborishTest(ArizaTestMixin, TestCase):
    """Bot orqali ariza yuborish: faqat ism, telefon va sinf so'raladi."""

    def url(self):
        return "/api/applications/"

    def test_ozod_authsiz_ariza_yuboriladi(self):
        """Ariza yuborish ochiq endpoint — bot JWT olmaydi."""
        anon = APIClient()
        javob = anon.post(
            self.url(),
            {
                "telegram_id": 111111,
                "fish": "Alisher Karimov",
                "telefon": "+998901234567",
                "sinf": "7-A",
            },
            format="json",
        )
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertEqual(Ariza.objects.count(), 1)

        ariza = Ariza.objects.get()
        self.assertEqual(ariza.holati, "kutmoqda")
        self.assertEqual(ariza.sinf, "7-A")
        self.assertIsNone(ariza.tasdiqlangan_sana)

    def test_sinf_majburiy(self):
        """Sinf bo'sh bo'lsa ariza yaratilmasligi kerak."""
        anon = APIClient()
        javob = anon.post(
            self.url(),
            {
                "telegram_id": 111111,
                "fish": "Alisher Karimov",
                "telefon": "+998901234567",
                "sinf": "   ",
            },
            format="json",
        )
        self.assertEqual(javob.status_code, 400)
        # config/exceptions.py xatolarni {error, detail} juftligiga yig'adi.
        self.assertIn("sinf", javob.data["detail"])
        self.assertEqual(Ariza.objects.count(), 0)

    def test_bot_yuboradigan_bo_sh_kasb_buzilmaydi(self):
        """Bot o'quvchi uchun `kasb: ""` yuboradi (o'qituvchilar uchun maydon) —
        bunday ariza "kasbni ko'rsating" xatosi bilan rad etilmasligi kerak."""
        anon = APIClient()
        javob = anon.post(
            self.url(),
            {
                "telegram_id": 111111,
                "fish": "Alisher Karimov",
                "telefon": "+998901234567",
                "rol": "oquvchi",
                "sinf": "7-A",
                "kasb": "",
            },
            format="json",
        )
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertEqual(Ariza.objects.get().kasb, "")

    def test_telefon_formati_tekshiriladi(self):
        anon = APIClient()
        javob = anon.post(
            self.url(),
            {
                "telegram_id": 111111,
                "fish": "Alisher Karimov",
                "telefon": "901234567",
                "sinf": "7-A",
            },
            format="json",
        )
        self.assertEqual(javob.status_code, 400)
        self.assertIn("telefon", javob.data["detail"])

    def test_kutmoqdagi_arizani_qayta_yuborib_bolmaydi(self):
        Ariza.objects.create(
            telegram_id=111111, fish="Alisher Karimov", telefon="+998901234567", sinf="7-A"
        )
        anon = APIClient()
        javob = anon.post(
            self.url(),
            {
                "telegram_id": 111111,
                "fish": "Alisher Karimov",
                "telefon": "+998901234567",
                "sinf": "7-A",
            },
            format="json",
        )
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data["error"], "ariza_kutmoqda")
        self.assertEqual(Ariza.objects.count(), 1)

    def test_allaqachon_azo_bo_lsa_rad_etiladi(self):
        Oquvchi.objects.create(
            fish="Alisher Karimov",
            telefon="+998901234567",
            telegram_id=111111,
            karta_raqami="LIB-2026-0001",
        )
        anon = APIClient()
        javob = anon.post(
            self.url(),
            {
                "telegram_id": 111111,
                "fish": "Alisher Karimov",
                "telefon": "+998901234567",
                "sinf": "7-A",
            },
            format="json",
        )
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data["error"], "allaqachon_azo")

    def test_ariza_holati_ozchik(self):
        """Holatni ko'rish ochiq endpoint — bot shu orqali tekshiradi."""
        Ariza.objects.create(
            telegram_id=111111,
            fish="Alisher Karimov",
            telefon="+998901234567",
            sinf="7-A",
            holati="bekor",
            izoh="Telefon noto'g'ri",
        )
        anon = APIClient()
        javob = anon.get("/api/applications/status/", {"telegram_id": 111111})
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["holati"], "bekor")
        self.assertEqual(javob.data["izoh"], "Telefon noto'g'ri")

    def test_ariza_yoq_holat_null_qaytaradi(self):
        anon = APIClient()
        javob = anon.get("/api/applications/status/", {"telegram_id": 999999})
        self.assertEqual(javob.status_code, 200)
        self.assertIsNone(javob.data["holati"])


class ArizaRuxsatTest(ArizaTestMixin, TestCase):
    """Ro'yxat ko'rish va qabul/rad etish faqat kutubxonachiga ochiq."""

    def setUp(self):
        super().setUp()
        self.ariza = Ariza.objects.create(
            telegram_id=111111, fish="Alisher Karimov", telefon="+998901234567", sinf="7-A"
        )

    def test_anonim_royxatni_kora_olmaydi(self):
        anon = APIClient()
        self.assertEqual(anon.get("/api/applications/").status_code, 401)

    def test_anonim_tasdiqlay_olmaydi(self):
        anon = APIClient()
        javob = anon.post(f"/api/applications/{self.ariza.pk}/approve/")
        self.assertEqual(javob.status_code, 401)
        self.ariza.refresh_from_db()
        self.assertEqual(self.ariza.holati, "kutmoqda")

    def test_anonim_rad_eta_olmaydi(self):
        anon = APIClient()
        javob = anon.post(f"/api/applications/{self.ariza.pk}/reject/")
        self.assertEqual(javob.status_code, 401)
        self.ariza.refresh_from_db()
        self.assertEqual(self.ariza.holati, "kutmoqda")

    def test_ro_yxat_filtrlari(self):
        Ariza.objects.create(
            telegram_id=222222,
            fish="Bekora Aliyeva",
            telefon="+998901234568",
            sinf="9-B",
            holati="bekor",
        )
        javob = self.client.get("/api/applications/", {"holati": "bekor"})
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["count"], 1)

        javob = self.client.get("/api/applications/", {"sinf": "7-A"})
        self.assertEqual(javob.data["count"], 1)

    def test_qidiruv_telefon_bo_yicha(self):
        javob = self.client.get("/api/applications/", {"search": "+998901234567"})
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["count"], 1)


class ArizaTasdiqlashTest(ArizaTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.ariza = Ariza.objects.create(
            telegram_id=111111,
            fish="Alisher Karimov",
            telefon="+998901234567",
            sinf="7-A",
        )

    def test_tasdiqlash_oquvchi_yaratadi_va_xabar_yuboradi(self):
        with self.xabarni_tekshir():
            javob = self.client.post(f"/api/applications/{self.ariza.pk}/approve/")

        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual(javob.data["holati"], "tasdiqlandi")

        oquvchi = Oquvchi.objects.get(telefon="+998901234567")
        self.assertEqual(oquvchi.telegram_id, 111111)
        self.assertEqual(oquvchi.fish, "Alisher Karimov")
        self.assertEqual(oquvchi.sinf, "7-A")
        self.assertTrue(oquvchi.karta_raqami.startswith("LIB-"))

        self.ariza.refresh_from_db()
        self.assertIsNotNone(self.ariza.tasdiqlangan_sana)

        # Telegram xabari aynan bitta marta, o'quvchining chat_id si ga ketadi.
        self.yuborish.assert_called_once()
        xabar = YUBORILGAN_XABARLAR[0]
        self.assertEqual(xabar["chat_id"], 111111)
        self.assertIn("tasdiqlandi", xabar["matn"])
        self.assertIn(oquvchi.karta_raqami, xabar["matn"])

    def test_tasdiqlashda_yuborilgan_sana_bosh_qolmaydi(self):
        self.client.post(f"/api/applications/{self.ariza.pk}/approve/")
        self.ariza.refresh_from_db()
        self.assertIsNotNone(self.ariza.tasdiqlangan_sana)
        self.assertLessEqual(self.ariza.tasdiqlangan_sana, now())

    def test_mavjud_oquvchining_telefoni_boglanadi(self):
        """Telefon bo'yicha mavjud o'quvchi topilsa, yangisiga karta ochilmaydi."""
        mavjud = Oquvchi.objects.create(
            fish="Eski Ism", telefon="+998901234567", karta_raqami="LIB-2026-0001"
        )
        with self.xabarni_tekshir():
            javob = self.client.post(f"/api/applications/{self.ariza.pk}/approve/")

        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual(Oquvchi.objects.count(), 1)
        mavjud.refresh_from_db()
        self.assertEqual(mavjud.telegram_id, 111111)
        self.assertEqual(mavjud.fish, "Alisher Karimov")
        self.assertEqual(mavjud.karta_raqami, "LIB-2026-0001")
        # Karta mavjud bo'lgani uchun "yangi karta berildi" qismi
        # xabarda bo'lmasligi kerak.
        self.assertNotIn("Sizga berilgan karta raqami", YUBORILGAN_XABARLAR[0]["matn"])

    def test_boshqa_telegramga_bog_langan_telefon_rad_etiladi(self):
        """Boshqa akkauntga tegishli telefon: akkauntni o'girtirib bo'lmasin."""
        Oquvchi.objects.create(
            fish="Boshqa Oquvchi",
            telefon="+998901234567",
            telegram_id=555555,
            karta_raqami="LIB-2026-0001",
        )
        javob = self.client.post(f"/api/applications/{self.ariza.pk}/approve/")

        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data["error"], "telefon_band")
        self.ariza.refresh_from_db()
        self.assertEqual(self.ariza.holati, "kutmoqda")
        self.yuborish.assert_not_called()
    def test_allaqachon_tasdiqlangan_ariza_qayta_tasdiqlanmaydi(self):
        self.client.post(f"/api/applications/{self.ariza.pk}/approve/")
        javob = self.client.post(f"/api/applications/{self.ariza.pk}/approve/")
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data["error"], "holat_notogri")

    def test_arizadagi_manzil_va_tugilgan_sana_oquvchiga_ko_chadi(self):
        self.ariza.tugilgan_sana = "2010-05-01"
        self.ariza.manzil = "Toshkent, Chilanzar"
        self.ariza.save()

        self.client.post(f"/api/applications/{self.ariza.pk}/approve/")

        oquvchi = Oquvchi.objects.get(telefon="+998901234567")
        self.assertEqual(str(oquvchi.tugilgan_sana), "2010-05-01")
        self.assertEqual(oquvchi.manzil, "Toshkent, Chilanzar")

    def test_xabar_matnida_html_escape_qilinadi(self):
        """Foydalanuvchi ismidagi teglar xabarni buzmasligi kerak."""
        self.ariza.fish = "<b>Ali</b> & <script>"
        self.ariza.save()

        with self.xabarni_tekshir():
            self.client.post(f"/api/applications/{self.ariza.pk}/approve/")

        self.assertEqual(len(YUBORILGAN_XABARLAR), 1)
        matn = YUBORILGAN_XABARLAR[0]["matn"]
        self.assertIn("&lt;b&gt;Ali&lt;/b&gt;", matn)
        self.assertNotIn("<script>", matn)


class ArizaRadEtishTest(ArizaTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.ariza = Ariza.objects.create(
            telegram_id=111111, fish="Alisher Karimov", telefon="+998901234567", sinf="7-A"
        )

    def test_rad_etish_holatni_o_zgartiradi_va_xabar_yuboradi(self):
        with self.xabarni_tekshir():
            javob = self.client.post(
                f"/api/applications/{self.ariza.pk}/reject/",
                {"izoh": "Telefon raqami noto'g'ri"},
                format="json",
            )

        self.assertEqual(javob.status_code, 200, javob.data)
        self.assertEqual(javob.data["holati"], "bekor")
        self.assertEqual(javob.data["izoh"], "Telefon raqami noto'g'ri")

        # Rad etilganda o'quvchi yaratilmasligi kerak.
        self.assertEqual(Oquvchi.objects.count(), 0)

        # Eng muhimi: o'quvchiga Telegram xabari borishi shart.
        self.yuborish.assert_called_once()
        xabar = YUBORILGAN_XABARLAR[0]
        self.assertEqual(xabar["chat_id"], 111111)
        self.assertIn("rad etildi", xabar["matn"])
        self.assertIn("Telefon raqami noto'g'ri", xabar["matn"])

    def test_sababsiz_rad_etilishi_mumkin(self):
        with self.xabarni_tekshir():
            javob = self.client.post(
                f"/api/applications/{self.ariza.pk}/reject/", {}, format="json"
            )
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["izoh"], "")
        self.yuborish.assert_called_once()

    def test_uzun_izoh_255_belgidan_osmasligi(self):
        javob = self.client.post(
            f"/api/applications/{self.ariza.pk}/reject/",
            {"izoh": "x" * 400},
            format="json",
        )
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(len(javob.data["izoh"]), 255)

    def test_rad_etilgandan_keyin_qayta_tasdiqlanmaydi(self):
        self.client.post(f"/api/applications/{self.ariza.pk}/reject/", {}, format="json")
        javob = self.client.post(f"/api/applications/{self.ariza.pk}/approve/")
        self.assertEqual(javob.status_code, 400)
        self.assertEqual(javob.data["error"], "holat_notogri")

    def test_rad_etilgan_arizani_qayta_yuborish_mumkin(self):
        """Rad etilgandan keyin o'quvchi yangi ariza yubora oladi."""
        self.client.post(f"/api/applications/{self.ariza.pk}/reject/", {}, format="json")

        anon = APIClient()
        javob = anon.post(
            "/api/applications/",
            {
                "telegram_id": 111111,
                "fish": "Alisher Karimov",
                "telefon": "+998901234567",
                "sinf": "8-A",
            },
            format="json",
        )
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertEqual(Ariza.objects.filter(holati="kutmoqda").count(), 1)


class OqituvchiArizaTest(ArizaTestMixin, TestCase):
    """`rol="oqituvchi"` arizalari: ism-familiya, telefon va kasb (fan)."""

    def url(self):
        return "/api/applications/"

    def yubor(self, **qoshimcha):
        ma_lumot = {
            "telegram_id": 111111,
            "fish": "Karimova Nilufar",
            "telefon": "+998901234567",
            "rol": "oqituvchi",
        }
        ma_lumot.update(qoshimcha)
        return APIClient().post(self.url(), ma_lumot, format="json")

    def test_kasb_bilan_ariza_qabul_qilinadi(self):
        javob = self.yubor(kasb="Matematika")
        self.assertEqual(javob.status_code, 201, javob.data)

        ariza = Ariza.objects.get()
        self.assertEqual(ariza.rol, "oqituvchi")
        self.assertEqual(ariza.kasb, "Matematika")
        self.assertIsNone(ariza.sinf)
        self.assertEqual(ariza.holati, "kutmoqda")

    def test_kasb_majburiy(self):
        javob = self.yubor()
        self.assertEqual(javob.status_code, 400)
        self.assertIn("kasb", javob.data["detail"])
        self.assertEqual(Ariza.objects.count(), 0)

    def test_bot_yuboradigan_bo_sh_sinf_buzilmaydi(self):
        """Bot o'qituvchi uchun `sinf: ""` yuboradi (u so'ramaydi) — bunday
        ariza "maydan bo'sh" xatosi bilan rad etilmasligi kerak."""
        javob = self.yubor(sinf="", kasb="Matematika")

        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertIsNone(Ariza.objects.get().sinf)

    def test_uzun_kasb_rad_etiladi(self):
        javob = self.yubor(kasb="x" * 61)
        self.assertEqual(javob.status_code, 400)
        self.assertIn("kasb", javob.data["detail"])

    def test_tasdiqlashda_karta_ochiladi_va_kasb_xabarida_korishi(self):
        ariza = Ariza.objects.create(
            telegram_id=111111,
            fish="Karimova Nilufar",
            telefon="+998901234567",
            rol="oqituvchi",
            kasb="Ona tili",
        )

        with self.xabarni_tekshir():
            javob = self.client.post(f"/api/applications/{ariza.pk}/approve/")

        self.assertEqual(javob.status_code, 200, javob.data)

        oquvchi = Oquvchi.objects.get(telefon="+998901234567")
        self.assertEqual(oquvchi.telegram_id, 111111)
        self.assertTrue(oquvchi.karta_raqami.startswith("LIB-"))
        # Sinf o'qituvchida bo'sh bo'ladi (None emas — CharField NOT NULL).
        self.assertEqual(oquvchi.sinf, "")

        self.yuborish.assert_called_once()
        xabar = YUBORILGAN_XABARLAR[0]
        self.assertIn("Ona tili", xabar["matn"])

    def test_tasdiqlashda_rol_va_kasb_oquvchiga_ko_chadi(self):
        """Tasdiqlangan o'qituvchi "O'qituvchilar" bo'limida ko'rinishi uchun
        `Oquvchi.rol` va `Oquvchi.kasb` to'ldirilishi kerak."""
        ariza = Ariza.objects.create(
            telegram_id=111111,
            fish="Karimova Nilufar",
            telefon="+998901234567",
            rol="oqituvchi",
            kasb="Ona tili",
        )

        with self.xabarni_tekshir():
            javob = self.client.post(f"/api/applications/{ariza.pk}/approve/")

        self.assertEqual(javob.status_code, 200, javob.data)
        oquvchi = Oquvchi.objects.get(telefon="+998901234567")
        self.assertEqual(oquvchi.rol, "oqituvchi")
        self.assertEqual(oquvchi.kasb, "Ona tili")

    def test_rol_filteri_ishlaydi(self):
        Ariza.objects.create(
            telegram_id=111111,
            fish="Alisher Karimov",
            telefon="+998901234567",
            sinf="7-A",
        )
        Ariza.objects.create(
            telegram_id=222222,
            fish="Karimova Nilufar",
            telefon="+998901234568",
            rol="oqituvchi",
            kasb="Fizika",
        )

        javob = self.client.get("/api/applications/", {"rol": "oqituvchi"})
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["count"], 1)
        self.assertEqual(javob.data["results"][0]["kasb"], "Fizika")

    def test_kasb_bo_yicha_qidiruv(self):
        Ariza.objects.create(
            telegram_id=222222,
            fish="Karimova Nilufar",
            telefon="+998901234568",
            rol="oqituvchi",
            kasb="Informatika",
        )
        javob = self.client.get("/api/applications/", {"search": "Informatika"})
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["count"], 1)


class ArizaAdminActionTest(ArizaTestMixin, TestCase):
    """Django admin orqali qabul/rad etish ham xabar yuborishi kerak."""

    def setUp(self):
        super().setUp()
        self.xodim.is_staff = True
        self.xodim.is_superuser = True
        self.xodim.save()
        self.client.force_login(self.xodim)

    def test_admin_tasdiqlash_xabar_yuboradi(self):
        from django.contrib.admin.sites import site

        ariza = Ariza.objects.create(
            telegram_id=111111, fish="Alisher Karimov", telefon="+998901234567", sinf="7-A"
        )
        admin = site._registry[Ariza]
        with self.xabarni_tekshir():
            admin.arizani_tasdiqlash(self._request(), Ariza.objects.filter(pk=ariza.pk))

        self.assertEqual(Oquvchi.objects.count(), 1)
        self.yuborish.assert_called_once()

    def test_admin_rad_etish_xabar_yuboradi(self):
        from django.contrib.admin.sites import site

        ariza = Ariza.objects.create(
            telegram_id=111111, fish="Alisher Karimov", telefon="+998901234567", sinf="7-A"
        )
        admin = site._registry[Ariza]
        with self.xabarni_tekshir():
            admin.arizani_rad_etish(self._request(), Ariza.objects.filter(pk=ariza.pk))

        ariza.refresh_from_db()
        self.assertEqual(ariza.holati, "bekor")
        self.yuborish.assert_called_once()
        self.assertIn("rad etildi", YUBORILGAN_XABARLAR[0]["matn"])

    def _request(self):
        """Admin action `message_user` ni chaqiradi — shuning uchun so'rovga
        session va xabarlar saqlagichi qo'shiladi."""
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        so_rov = RequestFactory().post("/admin/oquvchi/ariza/")
        so_rov.session = {}
        so_rov.user = self.xodim
        so_rov._messages = FallbackStorage(so_rov)
        return so_rov


class KartaRaqamiTest(TestCase):
    def test_karta_raqamlari_ketma_ket_bo_ladi(self):
        from .services import keyingi_karta_raqami

        self.assertEqual(keyingi_karta_raqami(), f"LIB-{now().year}-0001")
        Oquvchi.objects.create(fish="A", telefon="+998901234567", karta_raqami=keyingi_karta_raqami())
        self.assertEqual(keyingi_karta_raqami(), f"LIB-{now().year}-0002")

    def test_ariza_tasdiqlashda_karta_raqami_bo_sh_qolmaydi(self):
        """Bir nechta ariza tasdiqlanganda karta raqamlari takrorlanmasin."""
        xodim = User.objects.create_user(
            username="kutubxonachi", password="parol12345", full_name="K", rol="kutubxonachi"
        )
        client = APIClient()
        client.force_authenticate(xodim)

        for i in range(3):
            ariza = Ariza.objects.create(
                telegram_id=100 + i,
                fish=f"O'quvchi {i}",
                telefon=f"+9989012345{i:02d}",
                sinf="7-A",
            )
            javob = client.post(f"/api/applications/{ariza.pk}/approve/")
            self.assertEqual(javob.status_code, 200, javob.data)

        karta_raqamlari = list(Oquvchi.objects.values_list("karta_raqami", flat=True))
        self.assertEqual(len(karta_raqamlari), 3)
        self.assertEqual(len(set(karta_raqamlari)), 3, "karta raqamlari takrorlandi")


class OquvchiRolTest(ArizaTestMixin, TestCase):
    """"O'qituvchilar" bo'limi: `?rol=oqituvchi` filtri faqat o'qituvchilarni
    ko'rsatishi va o'qituvchi qo'shishda fan majburiy bo'lishi tekshiriladi."""

    def setUp(self):
        super().setUp()
        self.oquvchi = Oquvchi.objects.create(
            fish="Alisher Karimov", telefon="+998901234567", karta_raqami="LIB-2026-0001", sinf="7-A"
        )
        self.oqituvchi = Oquvchi.objects.create(
            rol="oqituvchi",
            fish="Karimova Nilufar",
            telefon="+998901234568",
            karta_raqami="LIB-2026-0002",
            kasb="Ona tili",
        )

    def test_rol_filtri_faqat_oqituvchilarni_qaytaradi(self):
        javob = self.client.get("/api/readers/", {"rol": "oqituvchi"})
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["count"], 1)
        self.assertEqual(javob.data["results"][0]["fish"], "Karimova Nilufar")

    def test_filtrsiz_ro_yxatda_ikkalasi_bor(self):
        javob = self.client.get("/api/readers/")
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["count"], 2)

    def test_oqituvchi_kartochkasida_kasb_qaytadi(self):
        javob = self.client.get(f"/api/readers/{self.oqituvchi.pk}/")
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(javob.data["rol"], "oqituvchi")
        self.assertEqual(javob.data["kasb"], "Ona tili")

    def test_oqituvchi_qo_shish_fan_bilan(self):
        javob = self.client.post(
            "/api/readers/",
            {
                "rol": "oqituvchi",
                "fish": "Rahimov Sardor",
                "telefon": "+998901234569",
                "kasb": "Fizika",
            },
            format="json",
        )
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertEqual(javob.data["rol"], "oqituvchi")
        self.assertEqual(javob.data["kasb"], "Fizika")
        self.assertEqual(javob.data["sinf"], "")

    def test_oqituvchi_fansiz_qabul_qilinmaydi(self):
        javob = self.client.post(
            "/api/readers/",
            {"rol": "oqituvchi", "fish": "Rahimov Sardor", "telefon": "+998901234570"},
            format="json",
        )
        self.assertEqual(javob.status_code, 400, javob.data)
        self.assertIn("kasb", str(javob.data))

    def test_oddiy_oquvchi_sinfi_bilan_qabul_qilinadi(self):
        javob = self.client.post(
            "/api/readers/",
            {"fish": "Nodirbek", "telefon": "+998901234571", "sinf": "9-B"},
            format="json",
        )
        self.assertEqual(javob.status_code, 201, javob.data)
        self.assertEqual(javob.data["rol"], "oquvchi")
