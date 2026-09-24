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
import logging

import aiohttp

import config

logger = logging.getLogger(__name__)


class ApiXato(Exception):
    """API dan kelgan {"error": kod, "detail": matn} formatidagi xato."""

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

    async def _sess(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def yopish(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _login(self):
        if not config.BOT_SERVICE_USERNAME or not config.BOT_SERVICE_PASSWORD:
            raise RuntimeError(
                "BOT_SERVICE_USERNAME / BOT_SERVICE_PASSWORD .env da ko'rsatilmagan. "
                "Django admin orqali rol='kutubxonachi' bilan xizmat akkaunti yarating."
            )
        sess = await self._sess()
        url = f"{config.API_BASE_URL}/auth/token/"
        payload = {
            "username": config.BOT_SERVICE_USERNAME,
            "password": config.BOT_SERVICE_PASSWORD,
        }
        async with sess.post(url, json=payload) as r:
            data = await r.json(content_type=None)
            if r.status != 200:
                raise RuntimeError(f"Bot xizmat akkauntiga kirib bo'lmadi: {data}")
            self._access = data["access"]
            self._refresh = data["refresh"]

    async def _tokenni_yangila(self):
        if not self._refresh:
            await self._login()
            return
        sess = await self._sess()
        url = f"{config.API_BASE_URL}/auth/token/refresh/"
        async with sess.post(url, json={"refresh": self._refresh}) as r:
            if r.status != 200:
                await self._login()
                return
            data = await r.json(content_type=None)
            self._access = data["access"]

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

        async with sess.request(
            method, url, params=params, json=json_data, headers=headers
        ) as r:
            try:
                data = await r.json(content_type=None)
            except Exception:
                data = {"error": "server_xatosi", "detail": await r.text()}

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

    # ---------- Kartani bog'lash ----------
    async def bind(self, telefon: str, karta_raqami: str, telegram_id: int):
        return await self._so_rov(
            "POST",
            "/readers/bind/",
            auth=False,
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
            auth=False,
            params={"telegram_id": telegram_id},
        )

    async def ariza_yubor(
        self,
        telegram_id: int,
        fish: str,
        telefon: str,
        *,
        tugilgan_sana: str | None = None,
        manzil: str = "",
    ):
        return await self._so_rov(
            "POST",
            "/applications/",
            auth=False,
            json_data={
                "telegram_id": telegram_id,
                "fish": fish,
                "telefon": telefon,
                "tugilgan_sana": tugilgan_sana,
                "manzil": manzil,
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
            auth=False,
            json_data={"kitob": kitob_id, "telegram_id": telegram_id},
        )

    async def navbatlarim(self, telegram_id: int):
        return await self._so_rov(
            "GET", "/reservations/my/", auth=False, params={"telegram_id": telegram_id}
        )

    async def navbat_javob(self, navbat_id: int, javob: str):
        return await self._so_rov(
            "POST",
            f"/reservations/{navbat_id}/respond/",
            auth=False,
            json_data={"javob": javob},
        )

    async def navbatdan_chiq(self, navbat_id: int):
        return await self._so_rov("DELETE", f"/reservations/{navbat_id}/", auth=False)

    # ---------- Mening kitoblarim / jarimalarim ----------
    async def kitoblarim(self, telegram_id: int):
        return await self._so_rov(
            "GET", "/loans/my/", auth=False, params={"telegram_id": telegram_id}
        )

    async def jarimalarim(self, telegram_id: int):
        return await self._so_rov(
            "GET", "/fines/my/", auth=False, params={"telegram_id": telegram_id}
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


api = ApiClient()