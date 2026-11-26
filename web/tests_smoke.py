"""To'liq E2E smoke test: foydalanuvchi panelida qilingan barcha asosiy amallar.

Oddiy unit testlar alohida xizmatlarni tekshiradi; bu test esa ro'yxatdan
o'tishdan tortib kitob berish, qaytarish, jarima, band, navbat, xabar va
PWA qobig'igacha bo'lgan butun zanjirni bitta oqimda HTTP orqali bosib o'tadi.
Agar biror endpoint frontend kutgan shaklda javob qaytarmasa, test darrov
ko'rsatadi.
"""
from datetime import date, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from organization.models import Organization
from user.models import XatolikXabari

User = get_user_model()


class ButunLoyihaSmokeTest(TestCase):
    """Panelning barcha bo'limlarini oxirigacha ishlatib ko'rish."""

    def setUp(self):
        # 1. Ro'yxatdan o'tish (ochiq endpoint) — test uchun yangi kutubxona.
        self.client = APIClient()
        javob = self.client.post(
            "/api/auth/register/",
            {
                "kutubxona_nomi": "Smoke test kutubxonasi",
                "turi": "library",
                "full_name": "Smoke Administrator",
                "telefon": "+998901234567",
                "password": "SmokeParol123!",
                "password_confirm": "SmokeParol123!",
            },
            format="json",
        )
        self.assertEqual(javob.status_code, 201, javob.data)
        self.org = Organization.objects.get(pk=javob.data["organization"]["id"])
        # Ro'yxatdan o'tishdan keyin tashkilot platforma tomonidan tasdiqlanadi.
        self.org.status = Organization.HOLAT_ACTIVE
        self.org.save(update_fields=["status"])
        self.admin = User.objects.get(pk=javob.data["user"]["id"])
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {javob.data['access']}",
            HTTP_X_ORGANIZATION_ID=str(self.org.pk),
        )

    def api(self, method, url, data=None, expected=200, **kwargs):
        # Qulaylik: GET da 3-argument query params (URL ga qo'shamiz — DRF
        # APIClient `params`-ni e'tiborga olmaydi), qolganlarida — so'rov tanasi.
        if data is not None and method == "get":
            from urllib.parse import urlencode

            url = f"{url}?{urlencode(data)}"
            data = None
        javob = getattr(self.client, method)(url, data, format="json", **kwargs)
        self.assertEqual(
            javob.status_code,
            expected,
            f"{method.upper()} {url}: kutilgan {expected}, olingan {javob.status_code}. "
            f"Javob: {getattr(javob, 'data', javob.content)}",
        )
        return javob.data

    def test_toliq_ish_oqimi(self):
        # --- 2. Kirish va profil -------------------------------------------------
        self.api("get", "/api/auth/me/")
        self.api("get", "/api/auth/organization/")
        self.api("get", "/api/auth/memberships/")
        login = self.api(
            "post",
            "/api/auth/token/",
            {"username": "+998901234567", "password": "SmokeParol123!"},
        )
        self.assertIn("access", login)
        self.api(
            "patch",
            "/api/auth/profile/",
            {"full_name": "Smoke Administrator Yangi"},
        )
        self.api(
            "post",
            "/api/auth/xatolik-xabari/",
            {"matn": "Smoke test xabari", "sahifa": "/", "tur": "qolda"},
            expected=201,
        )
        self.assertEqual(XatolikXabari.objects.filter(organization=self.org).count(), 1)
        self.api("get", "/api/auth/xatolik-xabari/")

        # --- 3. Xodimlar --------------------------------------------------------
        xodim = self.api(
            "post",
            "/api/staff/",
            {
                "username": "smoke_librarian",
                "full_name": "Smoke Kutubxonachi",
                "rol": "kutubxonachi",
                "telefon": "+998901111111",
                "password": "SmokeParol123!",
            },
            expected=201,
        )
        self.api("get", "/api/staff/")
        self.api("patch", f"/api/staff/{xodim['id']}/", {"is_active": False})
        self.api("patch", f"/api/staff/{xodim['id']}/", {"is_active": True})

        # --- 4. Kitoblar va nusxalar --------------------------------------------
        kitob = self.api(
            "post",
            "/api/books/",
            {
                "nomi": "Smoke kitob",
                "muallif": "Smoke Muallif",
                "janr": "badiiy",
                "nashr_yili": 2020,
            },
            expected=201,
        )
        kitob_id = kitob["id"]
        self.api("get", "/api/books/")
        self.api("get", f"/api/books/{kitob_id}/")
        self.api("get", "/api/books/search/", {"q": "Smoke"})
        self.api("patch", f"/api/books/{kitob_id}/", {"tavsif": "Tahrir qilindi"})

        nusxa = self.api(
            "post",
            "/api/copies/",
            {
                "kitob": kitob_id,
                "inventar_raqami": "SMK-001",
                "holati": "mavjud",
                "javon": "A-1",
                "qabul_sana": str(date.today()),
            },
            expected=201,
        )
        self.api("get", "/api/copies/")
        self.api("get", f"/api/copies/{nusxa['id']}/")
        self.api("patch", f"/api/copies/{nusxa['id']}/", {"javon": "B-2"})

        # --- 5. O'quvchi va o'qituvchi ------------------------------------------
        oquvchi = self.api(
            "post",
            "/api/readers/",
            {"rol": "oquvchi", "fish": "Ali Valiyev", "telefon": "+998902222222", "sinf": "7-B sinf"},
            expected=201,
        )
        oqituvchi = self.api(
            "post",
            "/api/readers/",
            {"rol": "oqituvchi", "fish": "Olim Karimov", "telefon": "+998903333333", "kasb": "Algebra"},
            expected=201,
        )
        self.assertEqual(oquvchi["sinf"], "7-B", "Sinf kanonik shaklga keltirilishi kerak")
        # Telegram ID faqat bot tomonidan bog'lanadi (serializer'da read-only),
        # xabar yuborish oqimini sinash uchun uni model orqali qo'yamiz.
        from oquvchi.models import Oquvchi

        Oquvchi.objects.filter(pk=oquvchi["id"]).update(telegram_id=999001)
        self.api("get", "/api/readers/", {"rol": "oquvchi"})
        self.api("get", "/api/readers/", {"search": "Ali"})
        self.api("get", f"/api/readers/{oquvchi['id']}/")
        self.api("patch", f"/api/readers/{oquvchi['id']}/", {"sinf": "8-A"})

        # --- 6. Arizalar: yaratish, filtrlash, tasdiqlash/rad etish --------------
        ariza = self.api(
            "post",
            "/api/applications/",
            {
                "telegram_id": 999011,
                "fish": "YangiOquvchi Testov",
                "telefon": "+998904444444",
                "rol": "oquvchi",
                "sinf": "9-A",
            },
            expected=201,
        )
        ariza_teacher = self.api(
            "post",
            "/api/applications/",
            {
                "telegram_id": 999012,
                "fish": "YangiOqituvchi Testov",
                "telefon": "+998905555555",
                "rol": "oqituvchi",
                "kasb": "Boshlang'ich",
            },
            expected=201,
        )
        self.api("get", "/api/applications/")
        self.api("get", "/api/applications/", {"holati": "kutmoqda"})
        self.api("get", "/api/applications/status/", {"telegram_id": 999011})
        self.api("post", f"/api/applications/{ariza_teacher['id']}/reject/", {"izoh": "Smoke rad"})
        tasdiqlangan = self.api("post", f"/api/applications/{ariza['id']}/approve/")
        self.assertEqual(tasdiqlangan["holati"], "tasdiqlandi")

        # --- 7. Berish va qaytarish ---------------------------------------------
        berish = self.api(
            "post",
            "/api/loans/",
            {"nusxa": nusxa["id"], "oquvchi": oquvchi["id"]},
            expected=201,
        )
        self.api("get", "/api/loans/")
        self.api("get", "/api/loans/overdue/")
        qaytarish = self.api("post", f"/api/loans/{berish['id']}/return/")
        self.assertTrue(qaytarish.get("muvaffaqiyatli", True))

        # O'qituvchiga ham berish (bitta Oquvchi jadvali).
        berish2 = self.api(
            "post",
            "/api/loans/",
            {"kitob": kitob_id, "oquvchi": oqituvchi["id"]},
            expected=201,
        )
        self.api("post", f"/api/loans/{berish2['id']}/return/")

        # --- 8. Jarimalar -------------------------------------------------------
        self.api("get", "/api/fines/")
        self.api("get", "/api/fines/", {"tolandimi": False})
        # Muddat o'tgan berish yaratib, jarima avtomatik hisoblanishini tekshiramiz.
        kechikkan = self.api(
            "post",
            "/api/loans/",
            {"kitob": kitob_id, "oquvchi": oquvchi["id"]},
            expected=201,
        )
        from berish.models import Berish

        Berish.objects.filter(pk=kechikkan["id"]).update(
            qaytarish_muddati=timezone.now() - timedelta(days=10)
        )
        self.api("post", f"/api/loans/{kechikkan['id']}/return/")
        jarimalar = self.api("get", "/api/fines/")
        self.assertTrue(jarimalar["results"], "Muddat o'tgan berishdan keyin jarima paydo bo'lishi kerak")
        self.api("post", f"/api/fines/{jarimalar['results'][0]['id']}/pay/")

        # --- 9. Band qilish (hold) ----------------------------------------------
        hold = self.api(
            "post",
            "/api/holds/",
            {"kitob": kitob_id, "oquvchi": oqituvchi["id"]},
            expected=201,
        )
        self.api("get", "/api/holds/")
        self.api("get", "/api/holds/my/", {"telegram_id": 999001})
        self.api("post", f"/api/holds/{hold['id']}/approve/", {"izoh": "Smoke tasdiq"})
        hold2 = self.api(
            "post",
            "/api/holds/",
            {"kitob": kitob_id, "oquvchi": oquvchi["id"]},
            expected=201,
        )
        self.api("post", f"/api/holds/{hold2['id']}/reject/", {"izoh": "Smoke rad"})

        # --- 10. Navbatlar ------------------------------------------------------
        navbat = self.api(
            "post",
            "/api/reservations/",
            {"kitob": kitob_id, "oquvchi": oquvchi["id"]},
            expected=201,
        )
        self.assertIn("orin", navbat)
        self.api("get", "/api/reservations/")
        self.api("get", f"/api/books/{kitob_id}/queue/")
        self.api("post", f"/api/reservations/{navbat['id']}/confirm/")
        navbat2 = self.api(
            "post",
            "/api/reservations/",
            {"kitob": kitob_id, "oquvchi": oqituvchi["id"]},
            expected=201,
        )
        self.api("delete", f"/api/reservations/{navbat2['id']}/", expected=204)

        # --- 11. Statistika -----------------------------------------------------
        self.api("get", "/api/stats/dashboard/")
        self.api("get", "/api/stats/top-books/")
        self.api("get", "/api/stats/recent-activity/")
        self.api("get", "/api/stats/ratings/activity/")

        # --- 12. Xabar yuborish va Telegram sozlamalari -------------------------
        self.api("get", "/api/messages/classes/", {"rol": "oquvchi"})
        with mock.patch("telegrambot.views.telegram_xabar_yubor", return_value=True) as yubor:
            natija = self.api(
                "post",
                "/api/messages/send/",
                {
                    "tur": "shaxs",
                    "rol": "oquvchi",
                    "oquvchi": oquvchi["id"],
                    "matn": "Smoke xabar",
                },
            )
            self.assertEqual(natija["yuborildi"], 1)
            yubor.assert_called_once()
        self.api("get", "/api/telegram/settings/")

        # --- 13. Kitobxonni o'chirish (faol berish bor — rad etilishi kerak) -----
        # Avvalgi oqimlarda nusxalar band/berishda ishlatilgan, yangi nusxa qo'shamiz.
        nusxa2 = self.api(
            "post",
            "/api/copies/",
            {
                "kitob": kitob_id,
                "inventar_raqami": "SMK-002",
                "holati": "mavjud",
                "qabul_sana": str(date.today()),
            },
            expected=201,
        )
        faol = self.api(
            "post",
            "/api/loans/",
            {"nusxa": nusxa2["id"], "oquvchi": oquvchi["id"]},
            expected=201,
        )
        natija = self.api(
            "post",
            "/api/readers/ochirish/",
            {"ids": [oquvchi["id"]]},
        )
        self.assertEqual(natija["ochirildi"], 0)
        self.assertEqual(natija["ochirilmadi"][0]["id"], oquvchi["id"])
        self.api("post", f"/api/loans/{faol['id']}/return/")
        natija = self.api("post", "/api/readers/ochirish/", {"ids": [oquvchi["id"]]})
        self.assertEqual(natija["ochirildi"], 1)

        # --- 14. PWA qobig'i ----------------------------------------------------
        html = self.client.get("/").content.decode()
        self.assertIn('name="viewport"', html)
        self.assertIn("width=device-width", html)
        self.assertIn('rel="manifest"', html)
        self.assertIn("/static/web/dist/manifest.json", html)
        sw = self.client.get("/sw.js")
        self.assertEqual(sw.status_code, 200)
        self.assertIn("javascript", sw["Content-Type"])
        sw_matn = b"".join(sw.streaming_content).decode()
        self.assertIn("kutubxona-static-", sw_matn)
        # Versiya oshirilganda bu test ham yangilanadi — eski kesh o'chirilishi
        # uchun PWA o'rnatilgan qurilmalarda yangi versiya darrov olinadi.
        self.assertIn("const VERSION = 'v4'", sw_matn)
