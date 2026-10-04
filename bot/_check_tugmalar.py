"""Telegram botning barcha tugmalari va API oqimlarini tekshiruvchi skript.

    python bot/_check_tugmalar.py            # statik tekshiruv (offline)
    python bot/_check_tugmalar.py --live     # + haqiqiy API ga so'rovlar

Statik qism (har doim ishlaydi, tarmoq talab qilmaydi):
  1. Pastdagi menyudagi har bir tugma matni router tomonidan ushlanadi
     (filtr haqiqiy `Message`/`CallbackQuery` obyekti bilan tekshiriladi —
     filtr ichki qurilmasiga bog'liq emas).
  2. `keyboards.py` da yaratiladigan har bir `callback_data` ushlanadi.
  3. Tugmalar Telegram cheklovlariga sig'adi (callback_data <= 64 bayt,
     tugma matni <= 64 belgi).
  4. Ariza bosqichida menyu tugmasi maydon sifatida tushib ketmaydi.
  5. Nusxasi yo'q ("asli") kitob matnida bo'sh `INV:` chiqmaydi.

Live qism (--live): bot ishlatadigan har bir API metodi haqiqiy javob
tuzilmasini tekshiradi — ayniqsa "Kategoriyalar" tugmasi (`/books/genres/`).
"""
import asyncio
import inspect
import re
import sys
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parent
ROOT = BOT_DIR.parent
sys.path.insert(0, str(BOT_DIR))

# Windows konsolida emoji chiqishi uchun (charmap cp1252 emoji va "o'"ni
# chiqarmaydi) — utf-8 ga o'tamiz.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from datetime import datetime  # noqa: E402

from aiogram.types import CallbackQuery, Chat, Message, Update, User  # noqa: E402

import keyboards as kb  # noqa: E402
from handlers import (  # noqa: E402
    kutubxonachi,
    navigatsiya,
    noma_lum,
    qidiruv,
    shaxsiy,
    start,
)
from states import Ariza, KutubxonachiQaytarish, Qidiruv  # noqa: E402

XATO = []

# main.py dagi ro'yxat tartibi. Buyruq va menyu tugmalari router'i BIRINCHI
# bo'lishi shart — aks holda ariza/qidiruv state handler'lari ularni yutib
# ketadi (batafsil: handlers/navigatsiya.py).
ROUTERLAR = (
    navigatsiya.router,
    start.router,
    qidiruv.router,
    shaxsiy.router,
    kutubxonachi.router,
    noma_lum.router,
)


def tekshir(shart: bool, matn: str) -> bool:
    if shart:
        print(f"  OK    {matn}")
    else:
        print(f"  XATO  {matn}")
        XATO.append(matn)
    return bool(shart)


class StubBot:
    """`Command` filtri `/buyruq@bot` shaklini tekshirish uchun bot obyekti."""

    async def me(self) -> User:
        return User(id=1, is_bot=True, first_name="bot", username="kutubxona_bot")


STUB_BOT = StubBot()

_raqam = 0


def _keyingi() -> int:
    global _raqam
    _raqam += 1
    return _raqam


def foydalanuvchi() -> User:
    return User(id=1, is_bot=False, first_name="Alisher")


def xabar(text: str | None) -> Update:
    """Real aiogram `Message` — filtrlar faqat haqiqiy obyekt bilan ishlaydi."""
    n = _keyingi()
    return Update(
        update_id=n,
        message=Message(
            message_id=n,
            date=datetime.now(),
            chat=Chat(id=1, type="private"),
            from_user=foydalanuvchi(),
            text=text,
        ),
    )


def bildirishnoma(data: str) -> Update:
    n = _keyingi()
    return Update(
        update_id=n,
        callback_query=CallbackQuery(
            id=str(n),
            from_user=foydalanuvchi(),
            chat_instance="1",
            data=data,
            message=Message(
                message_id=n,
                date=datetime.now(),
                chat=Chat(id=1, type="private"),
                text="inline",
            ),
        ),
    )


async def qaysi_handler(tur: str, hodisa: Update, raw_state: str | None = None):
    """Dispatcher mantiqini takrorlaydi: routerlar tartibida filtrlarni
    tekshirib, birinchi mos handler'ning nomini qaytaradi.

    Muhim: `HandlerObject.check()` **tuple** qaytaradi — `(mos, parametrlar)`.
    Agar `if await h.check(...)` deb yozilsa, mos kelmagan filtr ham truthy
    bo'lib chiqadi va tekshiruv har doim "OK" bo'lib chiqadi.
    """
    if tur == "message":
        obyekt = hodisa.message
    else:
        obyekt = hodisa.callback_query
    if obyekt is None:
        return None

    for router in ROUTERLAR:
        for h in getattr(router, tur).handlers:
            if h.filters is None:
                # Filtrsiz (noma_lum) handler oxirida — barcha joyda bo'lsa,
                # boshqa hech narsa tekshirilmay qolardi.
                continue
            try:
                mos, _ = await h.check(
                    obyekt,
                    bot=STUB_BOT,
                    event_update=hodisa,
                    event_from_user=obyekt.from_user,
                    event_chat=getattr(obyekt, "chat", None),
                    raw_state=raw_state,
                )
            except Exception:
                continue
            if mos:
                return h.callback.__name__
    return None


async def ushlanadimi(tur: str, hodisa: Update, raw_state: str | None = None) -> bool:
    return await qaysi_handler(tur, hodisa, raw_state) is not None


# ------------------------------------------------------------------ keyboards
# Quyidagi tugmalar bir nechta joyda chiqishi mumkin (sahifa navigatsiyasi,
# "orqaga" tugmalari, kitob kartochkasidagi "ro'yxatga qaytish") — ular
# doim bir xil handler'ga borishi kerak, shuning uchun ro'yxatga faqat
# bir marta qo'shiladi (2-boshqichda tekshiriladi).
TAKRORLAR: list[tuple[str, str]] = []


def barcha_tugmalar() -> dict[str, str]:
    """{callback_data: tavsif} — `keyboards.py` da yaratiladigan barcha
    inline tugmalar (real janr/kitob ma'lumotlari bilan)."""
    janrlar = [
        {"key": "badiiy", "label": "Badiiy adabiyot", "soni": 12},
        {"key": "fan", "label": "Fan", "soni": 8},
    ]
    kitoblar = [
        {"id": 1, "nomi": "O'tkan kunlar"},
        {"id": 2, "nomi": "Sarob " * 30},
    ]
    # 2-sahifa boshqa kitoblarni ko'rsatadi (callback_data takrorlanmasligi uchun)
    kitoblar_2 = [{"id": 101, "nomi": "Ufq"}, {"id": 102, "nomi": "Yulduzli tun"}]

    tugmalar = {}

    def yig(markup, manba: str):
        for qator in markup.inline_keyboard:
            for b in qator:
                if not b.callback_data:
                    continue
                if b.callback_data in tugmalar:
                    # Bir xil callback_data bir nechta joyda chiqishi mumkin
                    # (sahifa navigatsiyasi + "ro'yxatga qaytish"), lekin u
                    # doim bir xil handler'ga borishi kerak — bu 2-boshqichda
                    # tekshiriladi.
                    TAKRORLAR.append((b.callback_data, manba))
                    continue
                tugmalar[b.callback_data] = f"{manba} · {b.text}"

    yig(kb.ariza_rol_tugmalari(), "ariza_rol_tugmalari")
    yig(kb.kitob_batafsil_tugmasi(1), "kitob_batafsil_tugmasi")
    yig(kb.janr_tugmalari(janrlar), "janr_tugmalari")
    yig(kb.janr_kitob_tugmalari("badiiy", kitoblar, 1, 25), "janr_kitob_tugmalari s1")
    yig(kb.janr_kitob_tugmalari("badiiy", kitoblar_2, 2, 25), "janr_kitob_tugmalari s2")
    yig(
        kb.kitob_band_qilish_tugmalari(7, qaytish="jpage:badiiy:1"),
        "kitob_band_qilish_tugmalari",
    )
    yig(kb.navbatga_turish_tugmasi(7), "navbatga_turish_tugmasi")
    yig(kb.taklif_javob_tugmalari(3), "taklif_javob_tugmalari")
    yig(kb.navbatdan_chiqish_tugmasi(3), "navbatdan_chiqish_tugmasi")
    yig(kb.qaytarish_tasdiq_tugmasi(9), "qaytarish_tasdiq_tugmasi")
    return tugmalar


# ------------------------------------------------------------------- live API
async def live_tekshiruv() -> None:
    import config
    from api_client import ApiXato, api

    print(f"  API: {config.API_BASE_URL}")
    print(f"  Xizmat akkaunti: {config.BOT_SERVICE_USERNAME or '(SOZLANMAGAN)'}")

    natija = {}

    async def tekshir_(nomi, koruvchi, validatsiya):
        try:
            data = await koruvchi()
        except ApiXato as e:
            tekshir(False, f"{nomi}: API xato [{e.kod}] {e.detail}")
            return
        except Exception as e:  # noqa: BLE001
            tekshir(False, f"{nomi}: kutilmagan xato {type(e).__name__}: {e}")
            return
        natija[nomi] = data
        tekshir(bool(validatsiya(data)), f"{nomi}: {len(data) if hasattr(data, '__len__') else data} ta yozuv")

    def maydonlar(*nomlar):
        def ichki(data):
            if data and not isinstance(data, dict):
                kam = [n for n in nomlar if n not in data]
                if kam:
                    print(f"       yetishmayotgan maydonlar: {kam}")
                    return False
            return True

        return ichki

    await tekshir_(
        "GET /books/genres/  [📚 Kategoriyalar]",
        api.kitob_janrlar,
        lambda d: isinstance(d, list)
        and all(set(j) >= {"key", "label", "soni"} for j in d),
    )
    janrlar = natija.get("GET /books/genres/  [📚 Kategoriyalar]") or []
    if janrlar:
        janr = janrlar[0]["key"]
        await tekshir_(
            f"GET /books/?janr={janr}  [janr: tugmasi]",
            lambda: api.kitoblar_janrda(janr, sahifa=1),
            lambda d: isinstance(d, list) and all({"id", "nomi"} <= set(k) for k in d),
        )
        sahifali = natija.get(f"GET /books/?janr={janr}  [janr: tugmasi]") or []
        if sahifali:
            await tekshir_(
                f"GET /books/?janr={janr}&sahifa=2  [jpage: tugmasi]",
                lambda: api.kitoblar_janrda(janr, sahifa=2),
                lambda d: isinstance(d, list),
            )
            kid = sahifali[0]["id"]
            await tekshir_(
                f"GET /books/{kid}/  [jbook: tugmasi]",
                lambda: api.kitob_detail(kid),
                lambda d: {"nomi", "janr", "nusxalar"} <= set(d),
            )

    await tekshir_(
        "GET /books/search/  [🔍 Kitob qidirish]",
        lambda: api.kitob_qidir("o'tkan"),
        lambda d: isinstance(d, list) and all({"id", "nomi"} <= set(k) for k in d),
    )
    await tekshir_(
        "GET /auth/ariza/  [/start]",
        lambda: api.ariza_holati(1),
        maydonlar("holati"),
    )
    await tekshir_(
        "GET /loans/my/  [📚 Mening kitoblarim]",
        lambda: api.kitoblarim(1),
        lambda d: isinstance(d, list)
        and all(
            {"kitob_nomi", "qaytarish_muddati", "qolgan_kun", "inventar_raqami"} <= set(b)
            for b in d
        ),
    )
    await tekshir_(
        "GET /fines/my/  [💰 Jarimalarim]",
        lambda: api.jarimalarim(1),
        lambda d: isinstance(d, dict) and {"jarimalar", "umumiy_qarz"} <= set(d),
    )
    await tekshir_(
        "GET /reservations/my/  [⏳ Navbatlarim]",
        lambda: api.navbatlarim(1),
        lambda d: isinstance(d, list)
        and all({"kitob_nomi", "holati", "orin"} <= set(n) for n in d),
    )
    await tekshir_(
        "GET /copies/?inventar_raqami=  [/qaytar]",
        lambda: api.nusxa_topish("INV-000000"),
        lambda d: isinstance(d, (list, dict)),
    )

    await api.yopish()


# ---------------------------------------------------------------------- main
async def main() -> int:
    print("=" * 72)
    print("1. PASTDAGI MENYU TUGMALARI")
    print("=" * 72)
    menyu = kb.asosiy_menyu()
    menyu_tugmalari = [b.text for qator in menyu.keyboard for b in qator]
    tekshir(len(menyu_tugmalari) == 7, f"menyuda {len(menyu_tugmalari)} tugma")
    for t in menyu_tugmalari:
        tekshir(await ushlanadimi("message", xabar(t)), t)

    print()
    print("=" * 72)
    print("2. INLINE TUGMALAR (callback_data -> handler)")
    print("=" * 72)
    tugmalar = barcha_tugmalar()
    for data, tavsif in sorted(tugmalar.items()):
        tekshir(
            await ushlanadimi("callback_query", bildirishnoma(data)),
            f"{data[:44]:44}  <- {tavsif.split(' · ')[0]}",
        )

    print()
    print("=" * 72)
    print("3. TELEGRAM CHEKLOVLARI")
    print("=" * 72)
    for data in sorted(tugmalar):
        tekshir(len(data.encode()) <= 64, f"callback_data {len(data.encode()):>2}/64 bayt")
    for markup_nomi, markup in (
        (
            "janr_kitob_tugmalari",
            kb.janr_kitob_tugmalari("badiiy", [{"id": 1, "nomi": "Sarob " * 30}], 1, 1),
        ),
        (
            "janr_tugmalari",
            kb.janr_tugmalari([{"key": "a" * 40, "label": "L" * 40, "soni": 1}]),
        ),
    ):
        for qator in markup.inline_keyboard:
            for b in qator:
                tekshir(len(b.text) <= 64, f"{markup_nomi}: matn {len(b.text):>2}/64 belgi")

    print()
    print("=" * 72)
    print("4. FSM STATE ICHIDA BUYRUQ VA MENYU TUGMASI")
    print("=" * 72)
    # Buyruqlar va menyu tugmalari qaysi state'da bo'lishidan qat'i nazar
    # o'z handler'iga yetishi kerak. Aks holda `/bekor` "ism-familiya" bo'lib
    # ketadi, "📚 Kategoriyalar" esa ariza maydoniga yoziladi.
    kutilayotgan = {
        "/bekor": "bekor",
        "/qaytar": "qaytar",
        kb.KITOB_QIDIRISH: "menyu_qidirish",
        kb.KATEGORIYALAR: "menyu_kategoriya",
        kb.MENING_KITOBLARIM: "menyu_kitoblarim",
        kb.NAVBATLARIM: "menyu_navbatlarim",
        kb.JARIMALARIM: "menyu_jarimalarim",
    }
    holatlar = [
        (None, "holatsiz"),
        (Ariza.fish, "Ariza.fish"),
        (Ariza.telefon, "Ariza.telefon"),
        (Ariza.sinf, "Ariza.sinf"),
        (Ariza.kasb, "Ariza.kasb"),
        (Qidiruv.matn, "Qidiruv.matn"),
        (KutubxonachiQaytarish.inventar, "Kutubxonachi"),
    ]
    for raw_state, nomi in holatlar:
        for matn, kutilangan in kutilayotgan.items():
            olindi = await qaysi_handler("message", xabar(matn), raw_state)
            tekshir(
                olindi == kutilangan,
                f"{nomi:16} + {matn:22} -> {olindi} (kutilgan {kutilangan})",
            )

    # Qo'lda kiritilgan matn o'z state handler'iga yetishi kerak.
    for raw_state, kutilangan in (
        (Ariza.fish, "ariza_fish"),
        (Ariza.sinf, "ariza_sinf"),
        (Qidiruv.matn, "qidiruv_natija"),
        (KutubxonachiQaytarish.inventar, "inventar_qabul"),
        (None, "noma_lum_xabar"),
    ):
        olindi = await qaysi_handler("message", xabar("7-A sinf"), raw_state)
        tekshir(
            olindi == kutilangan,
            f"{str(raw_state or 'holatsiz'):16} + '7-A sinf'      -> {olindi}",
        )

    print()
    print("=" * 72)
    print("5. ARIZA BOSQICHIDA MENYU TUGMASI HIMOYASI")
    print("=" * 72)
    tekshir(
        start._menyu_tugmasi_bosilganmi(kb.KATEGORIYALAR)
        and start._menyu_tugmasi_bosilganmi(kb.JARIMALARIM)
        and start._menyu_tugmasi_bosilganmi(kb.NAVBATLARIM)
        and start._menyu_tugmasi_bosilganmi(kb.KITOB_QIDIRISH)
        and start._menyu_tugmasi_bosilganmi(kb.MENING_KITOBLARIM)
        and start._menyu_tugmasi_bosilganmi(kb.BANDLARIM)
        and start._menyu_tugmasi_bosilganmi(kb.MENYU),
        "barcha menyu tugmalari ariza maydoniga tushmaydi",
    )
    tekshir(
        not start._menyu_tugmasi_bosilganmi("7-A sinf")
        and not start._menyu_tugmasi_bosilganmi("Ona tili")
        and not start._menyu_tugmasi_bosilganmi("+998901234567")
        and not start._menyu_tugmasi_bosilganmi("Ali Valiyev"),
        "haqiqiy sinf/kasb/telefon/fish qiymatlari qabul qilinadi",
    )
    tekshir(
        inspect.iscoroutinefunction(kutubxonachi._ruxsat_berilganmi),
        "_ruxsat_berilganmi() async — xabar haqiqatan yuboriladi",
    )

    print()
    print("=" * 72)
    print("6. 'ASLI' KITOB MATNI")
    print("=" * 72)
    asl = shaxsiy._berish_qatori(
        {
            "kitob_nomi": "O'tkan kunlar",
            "inventar_raqami": "",
            "asli": True,
            "qaytarish_muddati": "2026-10-20",
            "qolgan_kun": 5,
        }
    )
    tekshir("INV:" not in asl, "bo'sh inventar 'INV: ' sifatida chiqmaydi")
    tekshir("Asli" in asl, "o'rniga 'Asli kitob' chiqadi")
    nusxa = shaxsiy._berish_qatori(
        {
            "kitob_nomi": "Sarob",
            "inventar_raqami": "INV-000412",
            "asli": False,
            "qaytarish_muddati": "2026-10-20",
            "qolgan_kun": -2,
        }
    )
    tekshir("INV-000412" in nusxa, "nusxa bor kitobda inventar raqami ko'rsatiladi")
    tekshir("o'tdi" in nusxa, "muddati o'tgani ogohlantiriladi")
    tekshir("Qolgan kun" in asl, "qolgan kun ko'rsatiladi")

    print()
    print("=" * 72)
    print("7. NUSXASI YO'Q KITOB — band qilish tasdiqlanadi, darhol berilmaydi")
    print("=" * 72)
    manba = (BOT_DIR / "handlers" / "qidiruv.py").read_text(encoding="utf-8")
    # Eski xabarlardagi «🕐 Band qilish» tugmasi ham `navbat_tur:` callback'ini
    # ishlatardi va u nusxasi yo'q kitobda kitobni DARHOL berar edi. Endi
    # `navbat_tur:` faqat eski "Band qilish" tugmalari uchun qolgan va band
    # so'rovi yaratadi; haqiqiy navbat esa alohida `navbat_qoldir:` orqali
    # ishlaydi. Quyidagi tekshiruvlar shu regressiaga qarshi.
    tekshir(
        '@router.callback_query(F.data.startswith("navbat_tur:"))' in manba
        and "_band_so_rovi_yubor(callback, kitob_id)" in manba,
        "eski `navbat_tur:` tugmasi band so'roviga yo'naltiradi",
    )
    tekshir(
        '@router.callback_query(F.data.startswith("navbat_qoldir:"))' in manba,
        "haqiqiy navbat uchun alohida `navbat_qoldir:` callback'i bor",
    )
    tekshir(
        "api.navbatga_tur(kitob_id, telegram_id)" in manba,
        "navbat API chaqirig'i faqat `navbat_qoldir:` handler'ida qolgan",
    )
    tekshir(
        "asli kitob berildi" not in manba,
        "asli kitob darhol berilishi xabari qoldirilmadi",
    )
    # Navbat tugmasi nusxasi yo'q kitoblarda ko'rsatilmasligi kerak.
    tekshir(
        "_navbat_mavjud" in manba,
        "nusxasi yo'q kitob kartasida navbat tugmasi ko'rsatilmaydi",
    )
    klav = (BOT_DIR / "keyboards.py").read_text(encoding="utf-8")
    tekshir(
        'callback_data=f"navbat_tur:' not in klav,
        "yangi tugmalarda `navbat_tur:` callback'i qolmaydi",
    )
    tekshir(
        'callback_data=f"band:{kitob_id}"' in klav,
        "«Band qilish» tugmasi `band:` callback'ini ishlatadi",
    )
    tekshir(
        "o'rindasiz" in manba,
        "faqat haqqiqiy navbatda 'o'rindasiz' deyiladi",
    )
    # Muddatdan oldin qaytarish xabari — servisda, barcha yo'llar uchun.
    servis = (ROOT / "apps" / "berish" / "services.py").read_text(encoding="utf-8")
    tekshir(
        "_erken_qaytarish_xabarini_yubor" in servis,
        "muddatdan oldin qaytarishda o'quvchiga xabar yuboriladi",
    )
    tekshir(
        "erken_qaytarish = berish.qaytarish_muddati > berish.qaytarilgan_sana" in servis,
        "muddatdan oldin qaytarish aniq qaytarish muddatidan aniqlanadi",
    )

    # `/api/holds/` pagination qiladi (frontend `data.results` o'qiydi), shuning
    # uchun bot ro'yxatni `results` dan ajratishi SHART — aks holda `/bandlar`
    # dict ustida `len()` va slicing ishlatib xato beradi.
    mijoz = (BOT_DIR / "api_client.py").read_text(encoding="utf-8")
    bandlar_dagi = mijoz.split("async def bandlar(")[1].split("async def")[0]
    tekshir(
        'data.get("results", [])' in bandlar_dagi,
        "bot `bandlar()` paginated javobdan `results` listini ajratadi",
    )
    xodim = (BOT_DIR / "handlers" / "kutubxonachi.py").read_text(encoding="utf-8")
    koritaz = xodim.split("async def bandlar_koritaz")[1].split("async def")[0]
    tekshir(
        "bandlar[:20]" in koritaz,
        "`/bandlar` ro'yxatni list sifatida kesib ko'rsatadi",
    )

    # Frontend `data.results` kutadi — backend pagination qilishi SHART.
    bandlar_view = (ROOT / "apps" / "kitob" / "views.py").read_text(encoding="utf-8")
    tekshir(
        "paginate_queryset" in bandlar_view.split("class BandQilishViewSet")[1],
        "backend `BandQilishViewSet` pagination qiladi (frontend `results` kutadi)",
    )
    frontend = ROOT / "frontend" / "src" / "pages" / "Bandlar.tsx"
    if frontend.exists():
        bandlar_sahifa = frontend.read_text(encoding="utf-8")
        tekshir(
            "data?.results" in bandlar_sahifa,
            "frontend «Bandlar» sahifasi `data.results` dan o'qiydi",
        )

    # ---------------------------------------------------------------
    # 8. BRENDING: emoji o'rniga yagona zamonaviy «logo» uslubi
    # ---------------------------------------------------------------
    print()
    print("=" * 72)
    print("8. XABAR USLUBI — «LOGO» VA TUGMA MATNLARI")
    print("=" * 72)

    brend = (BOT_DIR / "branding.py").read_text(encoding="utf-8")
    tekshir(
        "def logo(" in brend,
        "markaziy `branding.logo()` yordamchi funksiya bor",
    )
    tekshir(
        "KUTUBXONA" in brend,
        "brend nomi (`KUTUBXONA`) bitta joyda belgilangan",
    )
    tekshir(
        "def band_holati(" in brend,
        "band holatlari uchun yagona yordamchi (`band_holati`) bor",
    )

    # Band yaratilgan xabarda so'zgani olib tashlangan yozuvlar
    qidiruv_matni = (BOT_DIR / "handlers" / "qidiruv.py").read_text(encoding="utf-8")
    tekshir(
        "kuzatib turishingiz mumkin" not in qidiruv_matni,
        "«Bandlarim orqali kuzatib turishingiz mumkin» yozuvi olib tashlandi",
    )
    tekshir(
        "kutubxonachi yoki administrator" not in qidiruv_matni,
        "«kutubxonachi yoki administrator» yozuvi olib tashlandi",
    )
    tekshir(
        qidiruv_matni.count("Tasdiqlanganligi xabar qilinadi") == 2,
        "band xabarida «Tasdiqlanganligi xabar qilinadi» bor (ikkala joyda)",
    )

    yordam = (BOT_DIR / "utils.py").read_text(encoding="utf-8")
    tekshir(
        "administrator" not in yordam,
        "yordam matnida «administrator» yo'q",
    )
    tekshir(
        "Holatni «" not in yordam,
        "yordam matnida «Bandlarim orqali kuzatish» yo'q",
    )

    # Bandlarim bo'limi va kutubxonachi ro'yxati brendni ishlatadi
    shaxsiy_matn = (BOT_DIR / "handlers" / "shaxsiy.py").read_text(encoding="utf-8")
    tekshir(
        "logo(sarlavha='BANDLARIM')" in shaxsiy_matn,
        "«Bandlarim» bo'limi `branding.logo()` sarlavhasini ishlatadi",
    )
    kutubxonachi_matn = (BOT_DIR / "handlers" / "kutubxonachi.py").read_text(encoding="utf-8")
    tekshir(
        "logo(sarlavha=" in kutubxonachi_matn,
        "kutubxonachi band ro'yxati `branding.logo()` sarlavhasini ishlatadi",
    )

    # Eski emoji aralash xabarlar qolmasin
    for fayl, nomi in (
        (qidiruv_matni, "qidiruv.py"),
        (shaxsiy_matn, "shaxsiy.py"),
        (kutubxonachi_matn, "kutubxonachi.py"),
    ):
        tekshir(
            "🔒" not in fayl,
            f"{nomi} — eski «🔒» emojisi yo'q",
        )

    # Tugmalar: emoji tozalandi, matnlar qisqa va teng
    tugmalar = kb.band_tasdiq_tugmalari(7)
    matnlar = [t.text for t in tugmalar.inline_keyboard[0]]
    tekshir(
        matnlar == ["Tasdiqlash", "Rad etish"],
        f"tasdiqlash tugmalari toza va teng: {matnlar}",
    )
    tekshir(
        all(not m.startswith(("✅", "❌", "🚪", "📖", "🔒")) for m in matnlar),
        "tasdiqlash tugmalarida emoji yo'q",
    )
    bekor = kb.band_bekor_tugmasi(7)
    bekor_matn = bekor.inline_keyboard[0][0].text
    tekshir(
        bekor_matn == "Bekor qilish",
        f"bekor qilish tugmasi qisqa: '{bekor_matn}'",
    )
    tekshir(
        len(bekor_matn) <= 16,
        f"bekor tugmasi qisqa ({len(bekor_matn)} belgi, 16 dan ko'p emas)",
    )

    # Xabar yuborish botga va'da qilingan — API darajasida bajarilishi kerak
    band_servis = (ROOT / "apps" / "kitob" / "services.py").read_text(encoding="utf-8")
    tekshir(
        "_band_tasdiqlandi_xabarini_yubor" in band_servis,
        "tasdiqlashda o'quvchiga xabar yuboriladi",
    )
    tekshir(
        "_band_rad_etildi_xabarini_yubor" in band_servis,
        "rad etilganda o'quvchiga xabar yuboriladi",
    )
    tekshir(
        band_servis.count("transaction.on_commit") >= 2,
        "band xabarlari `transaction.on_commit` orqali yuboriladi",
    )

    # ------------------------------------------------ 9. menyu tugmalari
    print()
    print("=" * 72)
    print("9. YOZILAYOTGAN MAYDON YONIDAGI MENYU TUGMALARI")
    print("=" * 72)

    tekshir(
        kb.BOSHLASH == "▶️ Boshlash",
        f"Boshlash tugmasi bor: '{kb.BOSHLASH}'",
    )
    tekshir(
        kb.BOSHLASH in kb.ASOSIY_TUGMALAR,
        "Boshlash `ASOSIY_TUGMALAR` da — ariza maydoniga tushib ketmaydi",
    )

    klav = kb.ariza_klaviaturasi()
    matnlar = [b.text for qator in klav.keyboard for b in qator]
    tekshir(
        matnlar == [kb.BOSHLASH, kb.MENYU_YORDAM],
        f"ariza klaviaturasida Boshlash + Yordam bor: {matnlar}",
    )
    tekshir(
        kb.MENYU_YORDAM in matnlar,
        "Yordam tugmasi maydon yonida turadi",
    )

    tel_klav = kb.ariza_klaviaturasi(telefon_tugmasi=True)
    tel_matnlar = [b.text for qator in tel_klav.keyboard for b in qator]
    tekshir(
        tel_matnlar[0] == kb.TELEFON_YUBORISH,
        "telefon bosqichida kontakt tugmasi tepada",
    )
    tekshir(
        kb.BOSHLASH in tel_matnlar and kb.MENYU_YORDAM in tel_matnlar,
        "telefon bosqichida ham Boshlash + Yordam bor",
    )

    nav = Path(ROOT / "bot" / "handlers" / "navigatsiya.py").read_text(
        encoding="utf-8"
    )
    tekshir(
        "F.text == BOSHLASH" in nav,
        "navigatsiya.py da «Boshlash» tugmasi handler'i bor",
    )
    # Muhim: navigatsiya router'i state handler'laridan OLDIN ro'yxatlanishi
    # kerak, aks holda «Boshlash»/«Yordam» ariza maydoniga matn bo'lib ketadi.
    main_py = Path(ROOT / "bot" / "main.py").read_text(encoding="utf-8")
    router_tartibi = re.findall(r"dp\.include_router\((\w+)\.router\)", main_py)
    tekshir(
        bool(router_tartibi) and router_tartibi[0] == "navigatsiya",
        f"navigatsiya router'i birinchi ro'yxatlanadi ({router_tartibi[:2]})",
    )
    if "navigatsiya" in router_tartibi and "start" in router_tartibi:
        tekshir(
            router_tartibi.index("navigatsiya") < router_tartibi.index("start"),
            "menyu router'i ariza (start) router'idan oldin — tugma maydonga tushmaydi",
        )
    tekshir(
        "_yordam_ber" in nav,
        "yordam umumiy yordamchi orqali beriladi (bo'limlar uchun bir xil)",
    )
    _yordam_ber_manzili = nav.split("async def _yordam_ber")[1].split("async def boshlash_tugmasi")[0]
    tekshir(
        "_arizani_tugatish" not in _yordam_ber_manzili and "state.clear()" not in _yordam_ber_manzili.split("if joriy in YOZISH_BOSQICHLARI")[0],
        "yordam yozilayotgan ma'lumotni bekor qilmaydi",
    )

    # Yordam ariza/qidiruv/inventar bosqichida savolni qaytarishi kerak.
    start_py = Path(ROOT / "bot" / "handlers" / "start.py").read_text(
        encoding="utf-8"
    )
    tekshir(
        "def joriy_savol(" in start_py,
        "start.py da joriy savolni qaytaruvchi yordamchi bor",
    )
    tekshir(
        "ariza_klaviaturasi" in start_py,
        "ariza bosqichlarida maydon yonidagi klaviatura ishlatiladi",
    )
    tekshir(
        "klaviatura_olib_tashla()" not in start_py.split("async def _telefon_qabul")[1].split("async def ariza_sinf")[0],
        "telefon qabul qilingach klaviatura O'CHIRILMAYDI (menyu saqlanadi)",
    )

    qidiruv_py = Path(ROOT / "bot" / "handlers" / "qidiruv.py").read_text(
        encoding="utf-8"
    )
    tekshir(
        "QIDIRUV_SAVOLI" in qidiruv_py and "ariza_klaviaturasi()" in qidiruv_py,
        "qidiruv maydonida ham Boshlash + Yordam bor",
    )

    kutubxonachi_py = Path(
        ROOT / "bot" / "handlers" / "kutubxonachi.py"
    ).read_text(encoding="utf-8")
    tekshir(
        "INVENTAR_SAVOLI" in kutubxonachi_py
        and "ariza_klaviaturasi()" in kutubxonachi_py,
        "inventar maydonida ham Boshlash + Yordam bor",
    )

    # ------------------------------------------------ 10. matn imlosi
    print()
    print("=" * 72)
    print("10. MATN IMLOSI VA KONSISTENTLIGI")
    print("=" * 72)

    from utils import yordam_matni

    yordam_matni_tekshir = yordam_matni()
    tekshir(
        kb.BOSHLASH in yordam_matni_tekshir,
        "yordam matnida «Boshlash» tugmasi nomi keltirilgan",
    )
    tekshir(
        "bosib bo'lmaydi" not in yordam_matni_tekshir,
        "yordam matnida eskirgan «bosib bo'lmaydi» yozuvi yo'q",
    )
    tekshir(
        "Bandlarim" in yordam_matni_tekshir,
        "yordam matnida «Bandlarim» bo'limi ko'rsatilgan",
    )

    # Butun bot matnlarida kirill harf, tipograf apostrof va begona
    # yorliq qavslar bo'lmasin.
    kirill = []
    tipograf = []
    begona = []
    for fayl in sorted((ROOT / "bot").rglob("*.py")):
        if "__pycache__" in str(fayl) or fayl.name.startswith("_"):
            continue
        matn = fayl.read_text(encoding="utf-8-sig")
        for i, qator in enumerate(matn.splitlines(), 1):
            if re.search(r"[\u0400-\u04FF]", qator):
                kirill.append(f"{fayl.name}:{i}")
            if re.search(r"[\u2018\u2019]", qator):
                tipograf.append(f"{fayl.name}:{i}")
            # `「」` (yapon/korel) va `“”` — o'zbek matnida ishlatilmaydi.
            if re.search(r"[\u300c\u300d\u201c\u201d]", qator):
                begona.append(f"{fayl.name}:{i}")
    tekshir(not kirill, f"bot matnlarida kirill harf yo'q ({kirill or 'toza'})")
    tekshir(
        not tipograf,
        f"bot matnlarida tipograf apostrof yo'q ({tipograf or 'toza'})",
    )
    tekshir(
        not begona,
        f"bot matnlarida begona qavslar yo'q ({begona or 'toza'})",
    )

    # Noto'g'ri yozuvlar (avval aniqlangan xatolar).
    NOTO_GRI = [
        ("kartangizni bog'lang", "shaxsiy.py da eskirgan «kartangizni bog'lang»"),
        ("Quyidagilar to'g'ri keladi", "start.py da «Quyidagilar» noto'g'ri"),
        ("ISBN ni", "qidiruv.py da «ISBN ni» (ortiqcha probel)"),
        ("«Band qilish» ni", "qidiruv.py da «Band qilish» ni (ortiqcha probel)"),
        ("imtihonga...). ", "qidiruv.py da «imtihonga...). »"),
        ("band'so'rovini", "qidiruv.py da «band'so'rovini» (bo'sh joy yo'q)"),
        ("da.\n", "kutubxonachi.py da «X da» egalik qo'shimchasi"),
        ("yuboriladi — yoki", "kutubxonachi.py da noto'g'ri tire"),
        ("va sababi yuborildi", "kutubxonachi.py da «rad etilganligi va sababi»"),
    ]
    for izoh_matn, izoh in NOTO_GRI:
        topildi = [
            fayl.name
            for fayl in sorted((ROOT / "bot").rglob("*.py"))
            # `_` bilan boshlanadigan fayllar — tekshiruv skriptlari va
            # vaqtinchali yordamchilar (ularda qidirilayotgan so'zlar
            # "noto'g'ri yozuv" sifatida mavjud).
            if "__pycache__" not in str(fayl)
            and not fayl.name.startswith("_")
            and izoh_matn in fayl.read_text(encoding="utf-8-sig")
        ]
        tekshir(not topildi, f"{izoh} ({', '.join(topildi) or 'topilmadi'})")

    # Takror yozilgan xato xabarlari (uchala joyda) bitta joyga chiqarilgan.
    tekshir(
        qidiruv_py.count("xabarlar = {") == 0
        and "BAND_XATOLARI" in qidiruv_py
        and "NAVBAT_XATOLARI" in qidiruv_py,
        "band/navbat xato xabarlari bitta joydan olinadi (takror yo'q)",
    )

    # Xom ISO sana foydalanuvchiga ko'rsatilmasin.
    tekshir(
        "so_rov_sanasi'][:16]" not in kutubxonachi_py,
        "xom ISO sana (`[:16]`) ko'rsatilmaydi",
    )
    tekshir(
        "sana_vaqt(" in kutubxonachi_py,
        "sana `sana_vaqt()` yordamchisi orqali formatlanadi",
    )

    if "--live" in sys.argv:
        print()
        print("=" * 72)
        print("8. LIVE: bot API metodlari")
        print("=" * 72)
        await live_tekshiruv()

    print()
    print("=" * 72)
    if XATO:
        print(f"XATOLAR: {len(XATO)}")
        for x in XATO:
            print(f"  - {x}")
        return 1
    print("BARCHA TEKSHIROVLAR O'TDI")
    return 0
if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))