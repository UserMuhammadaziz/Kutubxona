"""
Django REST API bilan ishlash uchun yagona darvoza.

- Ba'zi endpointlar (readers/bind, loans/my, reservations/*, fines/my) hech
  qanday autentifikatsiya talab qilmaydi — o'quvchi kim ekani telegram_id
  orqali aniqlanadi.
- Boshqalari (books/search, books/{id}/, copies/..., loans/{id}/return/ va
  h.k.) IsAuthenticated/IsLibrarian talab qiladi — bot BOT_SERVICE_USERNAME/
  PASSWORD bilan /api/auth/token/ orqali JWT olib, shu tokenni ishlatadi.
- Server har doim xato holatida {"error": kod, "detail": matn} qaytaradi —
  shuni ApiXato istisnosiga aylantiramiz, handler'lar kodga qarab aniq
  xabar ko'rsatadi.
"""
import asyncio
import json
import logging

import aiohttp

import config

logger = logging.getLogger(__name__)

class ApiXato(Exception):
    """API dan kelgan {"error": kod, "detail": matn} formatidagi xato.

    Xizmat akkauntiga kirish yoki serverga ulanish xatolari ham shu
    istisnoga aylantiriladi — aks holda handler'lardagi `except ApiXato`
    ishlamay, butun oqim jim qolib ketardi (masalan "Kategoriyalar"
    tugmasi hech narsa bermaydi)."""

    def __init__(self, kod: str, detail: str, status: int = 400):
        self.kod = kod
        self.detail = detail
        self.status = status
        super().__init__(f"{kod}: {detail}")

class ApiClient:
    def __init__(self):
        self._session: aiohttp.ClientSession | None = None
        self._access: str | None = None
        self._refresh: str | None = None

    # Server javob bermasa, aiohttp cheksiz kutib qolmasin — aks holda
    # bitta so'rov butun botni (barcha handler'larni) to'xtatib qo'yadi.
    SOVOTME_VAQTI = aiohttp.ClientTimeout(total=20)

    async def _sess(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.SOVOTME_VAQTI)
        return self._session

    async def yopish(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _login(self):
        if not config.BOT_SERVICE_USERNAME or not config.BOT_SERVICE_PASSWORD:
            raise ApiXato(
                "xizmat_akkount_yoq",
                "Bot xizmat akkaunti sozlanmagan (.env da BOT_SERVICE_USERNAME "
                "va BOT_SERVICE_PASSWORD kerak)",
            )
        sess = await self._sess()
        url = f"{config.API_BASE_URL}/auth/token/"
        payload = {
            "username": config.BOT_SERVICE_USERNAME,
            "password": config.BOT_SERVICE_PASSWORD,
        }
        try:
            async with sess.post(url, json=payload) as r:
                status = r.status
                # Matnni avval o'qiymiz: JSON bo'lmasa ham xato matni
                # saqlanib qoladi (ikkinchi marta `r.text()` o'qib bo'lmaydi).
                qom = await r.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as xato:
            raise ApiXato(
                "server_ga_ulab_bolmadi", f"Serverga ulanib bo'lmadi: {xato}"
            ) from xato

        if status != 200:
            # Bu holatda butun bot ishlamaydi (kategoriya, qidiruv, kitob
            # kartochkasi...). Foydalanuvchiga tushunarli xabar beramiz va
            # sababni log'ga yozamiz.
            logger.error("Bot xizmat akkauntiga kirib bo'lmadi: %s %s", status, qom)
            raise ApiXato(
                "xizmat_akkount_kirish",
                "Bot serverga kira olmadi. Kutubxonachiga xabar bering "
                "(bot xizmat akkaunti tekshirilishi kerak)",
                status,
            )

        try:
            data = json.loads(qom)
            self._access = data["access"]
            self._refresh = data["refresh"]
        except (ValueError, KeyError, TypeError) as xato:
            logger.error("Token javobi kutilmagan ko'rinishda: %s", xato)
            raise ApiXato(
                "server_ga_ulab_bolmadi",
                "Server javobi noto'g'ri. Kutubxonachiga xabar bering.",
            ) from xato

    async def _tokenni_yangila(self):
        """Muddati o'tgan access token'ni yangilaydi.

        Refresh token ham ishlamasa (`401`/JSON buzilgan/server o'chgan)
        to'liq qayta login qilamiz — aks holda keyingi har bir so'rov
        yana 401 berib, foydalanuvchi hech qanday javob olmay qolardi.
        """
        self._access = None
        if not self._refresh:
            await self._login()
            return
        sess = await self._sess()
        url = f"{config.API_BASE_URL}/auth/token/refresh/"
        try:
            async with sess.post(url, json={"refresh": self._refresh}) as r:
                if r.status != 200:
                    await self._login()
                    return
                data = json.loads(await r.text())
                self._access = data["access"]
        except ApiXato:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, KeyError) as xato:
            logger.warning("Token yangilanmadi, qayta login qilinadi: %s", xato)
            await self._login()

    async def _headers(self, auth: bool) -> dict:
        if not auth:
            return {}
        if not self._access:
            await self._login()
        return {"Authorization": f"Bearer {self._access}"}

    async def _so_rov(
        self, method: str, path: str, *, auth=True, params=None, json_data=None, qayta=True
    ):
        sess = await self._sess()
        url = f"{config.API_BASE_URL}{path}"
        headers = await self._headers(auth)

        try:
            async with sess.request(
                method, url, params=params, json=json_data, headers=headers
            ) as r:
                # DELETE va ba'zi endpointlar 204 No Content qaytaradi —
                # JSON yo'q. `r.json()` bundan KeyError/ValueError beradi
                # va xato bo'lmagan javob "server_xatosi" deb ko'rinardi.
                #
                # Tanavli javoblarda (`Transfer-Encoding: chunked`)
                # `content_length` None bo'ladi — shuning uchun haqiqiy
                # tanani o'qib, bo'sh ekanini keyin tekshiramiz.
                qom = await r.text()

                if r.status == 204 or not qom.strip():
                    data = {}
                else:
                    try:
                        data = json.loads(qom)
                    except ValueError:
                        data = {"error": "server_xatosi", "detail": qom[:500]}

                if r.status == 401 and auth and qayta:
                    await self._tokenni_yangila()
                    return await self._so_rov(
                        method, path, auth=auth, params=params, json_data=json_data, qayta=False
                    )

                if r.status >= 400:
                    if isinstance(data, dict):
                        kod = data.get("error", "xato")
                        detail = data.get("detail", str(data))
                        if isinstance(kod, list):
                            kod = kod[0] if kod else "xato"
                        if isinstance(detail, list):
                            detail = detail[0] if detail else str(detail)
                    else:
                        kod, detail = "xato", str(data)
                    raise ApiXato(kod, detail, r.status)

                return data
        except ApiXato:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as xato:
            # Server o'chgan / internet uzilgan / javob kelmadi —
            # foydalanuvchi hech narsa ko'rmasligi o'rniga aniq xabar.
            raise ApiXato("server_ga_ulab_bolmadi", f"Serverga ulanib bo'lmadi: {xato}") from xato

    # ---------- Kartani bog'lash ----------
    async def bind(self, telefon: str, karta_raqami: str, telegram_id: int):
        return await self._so_rov(
            "POST",
            "/readers/bind/",
            json_data={
                "telefon": telefon,
                "karta_raqami": karta_raqami,
                "telegram_id": telegram_id,
            },
        )

    # ---------- A'zolik arizasi ----------
    async def ariza_holati(self, telegram_id: int):
        return await self._so_rov(
            "GET",
            "/applications/status/",
            params={"telegram_id": telegram_id},
        )

    async def ariza_yubor(
        self,
        telegram_id: int,
        fish: str,
        telefon: str,
        rol: str = "oquvchi",
        sinf: str = "",
        kasb: str = "",
    ):
        """POST /applications/ — a'zolik arizasi.

        Rolga qarab bitta qo'shimcha maydon to'ladi:
        • oquvchi    → `sinf` (masalan: 7-A)
        • oqituvchi  → `kasb` (o'qitayotgan fan, masalan: Matematika)
        """
        return await self._so_rov(
            "POST",
            "/applications/",
            json_data={
                "telegram_id": telegram_id,
                "fish": fish,
                "telefon": telefon,
                "rol": rol,
                "sinf": sinf,
                "kasb": kasb,
            },
        )

    # ---------- Kitob qidiruv ----------
    async def kitob_qidir(self, q: str):
        return await self._so_rov("GET", "/books/search/", params={"q": q})

    async def kitob_detail(self, kitob_id: int):
        return await self._so_rov("GET", f"/books/{kitob_id}/")

    async def kitob_janrlar(self):
        return await self._so_rov("GET", "/books/genres/")

    async def kitoblar_janr_boicha(self, janr: str, page: int = 1):
        """Berilgan janrdagi kitoblar ro'yxati (sahifa bo'yicha varaqlanadi).
        Sahifa o'lchami serverda PAGE_SIZE (20) — botda bitta ekranga to'g'ri keladi."""
        data = await self._so_rov("GET", "/books/", params={"janr": janr, "page": page})
        return data.get("results", []), data.get("count", 0)

    # ---------- Navbat ----------
    async def navbatga_tur(self, kitob_id: int, telegram_id: int):
        return await self._so_rov(
            "POST",
            "/reservations/",
            json_data={"kitob": kitob_id, "telegram_id": telegram_id},
        )

    async def navbatlarim(self, telegram_id: int):
        return await self._so_rov(
            "GET", "/reservations/my/", params={"telegram_id": telegram_id}
        )

    async def navbat_javob(self, navbat_id: int, javob: str):
        return await self._so_rov(
            "POST",
            f"/reservations/{navbat_id}/respond/",
            json_data={"javob": javob},
        )

    async def navbatdan_chiq(self, navbat_id: int):
        return await self._so_rov("DELETE", f"/reservations/{navbat_id}/")

    # ---------- Mening kitoblarim / jarimalarim ----------
    async def kitoblarim(self, telegram_id: int):
        return await self._so_rov(
            "GET", "/loans/my/", params={"telegram_id": telegram_id}
        )

    async def jarimalarim(self, telegram_id: int):
        return await self._so_rov(
            "GET", "/fines/my/", params={"telegram_id": telegram_id}
        )

    # ---------- Kutubxonachi: qaytarib olish (ixtiyoriy) ----------
    async def nusxa_qidir(self, inventar_raqami: str):
        """/copies/ pagination qilar edi — botga kerakli results (list) qaytariladi."""
        data = await self._so_rov(
            "GET", "/copies/", params={"inventar_raqami": inventar_raqami}
        )
        return data.get("results", []) if isinstance(data, dict) else data

    async def nusxa_detail(self, nusxa_id: int):
        return await self._so_rov("GET", f"/copies/{nusxa_id}/")

    async def kitobni_qaytar(self, berish_id: int):
        return await self._so_rov("POST", f"/loans/{berish_id}/return/")

    # ---------- Band qilish (saqlab qo'yish) ----------
    async def band_qil(self, kitob_id: int, telegram_id: int, izoh: str = ""):
        """POST /holds/ — kitobni band qilish so'rovi.

        So'rov yaratilgach kitob tasdiqlanmaguncha hech kimga berilmaydi;
        tasdiqlashni faqat kutubxonachi yoki administrator qiladi
        (`/holds/{id}/approve/`)."""
        return await self._so_rov(
            "POST",
            "/holds/",
            json_data={"kitob": kitob_id, "telegram_id": telegram_id, "izoh": izoh},
        )

    async def bandlarim(self, telegram_id: int):
        return await self._so_rov("GET", "/holds/my/", params={"telegram_id": telegram_id})

    async def band_bekor_qil(self, band_id: int, telegram_id: int):
        return await self._so_rov(
            "POST", f"/holds/{band_id}/cancel/", json_data={"telegram_id": telegram_id}
        )

    async def bandlar(self, holati: str = "kutmoqda"):
        """GET /holds/?holati= — kutubxonachi uchun ro'yxat (botda ruxsat
        BOT_ADMIN_CHAT_IDS orqali tekshiriladi).

        `/holds/` endi pagination qiladi (`{count, results}`, frontend shu
        shaklda kutadi), shuning uchun botga kerakli `results` listi
        ajratib beriladi — xuddi `nusxa_qidir()` kabi."""
        data = await self._so_rov("GET", "/holds/", params={"holati": holati})
        return data.get("results", []) if isinstance(data, dict) else data

    async def bandni_tasdiqla(self, band_id: int, izoh: str = ""):
        return await self._so_rov(
            "POST", f"/holds/{band_id}/approve/", json_data={"izoh": izoh}
        )

    async def bandni_rad_et(self, band_id: int, izoh: str = ""):
        return await self._so_rov(
            "POST", f"/holds/{band_id}/reject/", json_data={"izoh": izoh}
        )

api = ApiClient()
