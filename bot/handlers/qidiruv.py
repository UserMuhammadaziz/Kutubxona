import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import branding as b
from api_client import ApiXato, api
from handlers import shaxsiy
from keyboards import (
    ASOSIY_TUGMALAR,
    BANDLARIM,
    JARIMALARIM,
    KATEGORIYALAR,
    KITOB_QIDIRISH,
    MENING_KITOBLARIM,
    NAVBATLARIM,
    band_bekor_tugmasi,
    janr_kitob_tugmalari,
    janr_tugmalari,
    kitob_batafsil_tugmasi,
    kitob_band_qilish_tugmalari,
)
from states import Qidiruv
from utils import x, xabarni_tahrirlash

router = Router(name="qidiruv")
logger = logging.getLogger(__name__)

KO_RSATILADIGAN_SONI = 10

# Janr sahifasi: bitta tugma bir qatorda, bo'yiga 10 tasi — bir ekranda 10 ta kitob.
JANR_QATOR_SONI = 1
JANR_QATORLAR = 10
# Server /api/books/ PARK sahifasida 20 ta kitob qaytaradi (config/settings.py PAGE_SIZE).
JANR_API_SAHIFA_O_LCHAMI = 20

_janr_label_lar = {}

# Band va navbat so'rovlarida keladigan bir xil API xatolari. Uch handler'da
# takror yozilgan edi — matn bir marta o'zgartirilsa, uchala joy ham
# yangilanishini kafolatlaymiz.
BAND_XATOLARI = {
    "oquvchi_topilmadi": "Avval /start orqali ro'yxatdan o'ting.",
    "topilmadi": "Avval /start orqali ro'yxatdan o'ting.",
    "oquvchi_bloklangan": "Sizning kartangiz bloklangan.",
    "allaqachon_band_qilingan": "Bu kitob boshqa o'quvchi uchun band qilingan.",
    "allaqachon_berilgan": "Bu kitob allaqachon sizda bor.",
}

NAVBAT_XATOLARI = {
    **BAND_XATOLARI,
    "allaqachon_navbatda": "Siz bu kitobga allaqachon navbatdasiz.",
    "barcha_nusxalar_berilgan": "Bu kitobning nusxalari hozir berilgan.",
}

# Kategoriya tanlash xabari ikki handler'da takror yozilgan edi.
KATEGORIYA_SAVOLI = "📚 Kategoriyani tanlang:"

# Qidiruv maydoni savoli — `navigatsiya.py` «❓ Yordam»dan keyin shu
# savolni qaytaradi.
QIDIRUV_SAVOLI = "Kitob nomi, muallif yoki ISBNni yozing:"


async def _menyu_tugmasi_bo_lsa(message: Message, matn: str) -> None:
    """Qidiruv maydoniga bo'lim tugmasi matni keldi — shu bo'limni ochamiz.

    Bo'lim tugmalari matn yuboradi, shuning uchun ular qidiruv so'ziga
    tushmasligi SHART. Holat allaqach tozalandi (`qidiruv_natija` boshida),
    keyin foydalanuvchi «Kitob qidirish»ni qayta bosmasdan boshqa bo'limga
    o'tishi mumkin."""
    if matn == KATEGORIYALAR:
        await kategoriyalar(message)
        return

    bo_limlar = {
        MENING_KITOBLARIM: shaxsiy.kitoblarim,
        NAVBATLARIM: shaxsiy.navbatlarim,
        BANDLARIM: shaxsiy.bandlarim,
        JARIMALARIM: shaxsiy.jarimalarim,
    }
    funksiya = bo_limlar.get(matn)
    if funksiya:
        await funksiya(message)


async def _janr_label(janr_key: str) -> str:
    """Janr kalitini chiroyli nomiga aylantiradi (genres API dan, bir marta)."""
    if janr_key not in _janr_label_lar:
        try:
            janrlar = await api.kitob_janrlar()
            _janr_label_lar.update({j["key"]: j["label"] for j in janrlar})
        except ApiXato:
            # Kalit nomi o'zi chiqadigan zaxira sifatida qoladi.
            logger.warning("Janr nomlari yuklanmadi, kalit ishlatiladi")
    return _janr_label_lar.get(janr_key, janr_key)


async def _janr_sahifa_kitoblari(janr: str, sahifa: int):
    """Bot sahifasi (10 ta kitob) ni API sahifalari (20 ta) ga moslaydi.

    `nisbat` nolga bo'lishidan himoya qilinadi: aks holda
    `JANR_QATORLAR > JANR_API_SAHIFA_O_LCHAMI` bo'lganda `ZeroDivisionError`
    chiqar va butun janr bo'limi ishlamay qolardi."""
    nisbat = max(1, JANR_API_SAHIFA_O_LCHAMI // JANR_QATORLAR)
    api_sahifa = (sahifa - 1) // nisbat + 1
    boshi = ((sahifa - 1) % nisbat) * JANR_QATORLAR
    kitoblar, jami = await api.kitoblar_janr_boicha(janr, page=api_sahifa)
    return kitoblar[boshi : boshi + JANR_QATORLAR], jami


@router.message(F.text == KITOB_QIDIRISH)
async def qidiruv_boshla(message: Message, state: FSMContext):
    """Pastdigi «Kitob qidirish» tugmasi (yoki `/qidiruv` buyrug'i).

    Tugma allaqach qidiruv holatida bosilsa, foydalanuvchi «Kitob qidirish»
    so'zini qidirib topmaydi — shuning uchun savolni qayta ko'rsatamiz."""
    if await state.get_state() == Qidiruv.matn.state:
        await message.answer(QIDIRUV_SAVOLI)
        return

    await state.set_state(Qidiruv.matn)
    await message.answer(QIDIRUV_SAVOLI)


@router.message(Qidiruv.matn)
async def qidiruv_natija(message: Message, state: FSMContext):
    q = (message.text or "").strip()
    await state.clear()

    # Bo'lim tugmalari ham matn yuboradi — ular qidiruv so'zi EMAS.
    if q in ASOSIY_TUGMALAR:
        await _menyu_tugmasi_bo_lsa(message, q)
        return

    if not q:
        await message.answer("Iltimos, qidiruv so'zini kiriting.")
        return

    try:
        natijalar = await api.kitob_qidir(q)
    except ApiXato as e:
        await message.answer(f"Qidiruvda xatolik: {x(e.detail)}")
        return

    if not natijalar:
        await message.answer("❌ Kitob topilmadi. Boshqa nom bilan urinib ko'ring.")
        return

    for kitob in natijalar[:KO_RSATILADIGAN_SONI]:
        matn = (
            f"📖 <b>{x(kitob.get('nomi'))}</b> — {x(kitob.get('muallif'))} "
            f"({x(kitob.get('nashr_yili'))})\n"
            f"Mavjud: {kitob.get('mavjud_nusxalar') or 0} / "
            f"{kitob.get('jami_nusxalar') or 0}"
        )
        await message.answer(
            matn, reply_markup=kitob_batafsil_tugmasi(kitob["id"])
        )

    if len(natijalar) > KO_RSATILADIGAN_SONI:
        await message.answer(
            f"Jami {len(natijalar)} ta natija topildi. "
            "Aniqroq so'rov bilan qayta izlang."
        )


@router.message(F.text == KATEGORIYALAR)
async def kategoriyalar(message: Message):
    try:
        janrlar = await api.kitob_janrlar()
    except ApiXato as e:
        await message.answer(
            f"Kategoriyalarni yuklab bo'lmadi: {x(e.detail)}\n\n"
            "Bir ozdan keyin yana urinib ko'ring yoki /start bosing."
        )
        return

    if not janrlar:
        await message.answer("Hozircha kutubxonada kitoblar yo'q.")
        return

    await message.answer(KATEGORIYA_SAVOLI, reply_markup=janr_tugmalari(janrlar))


async def _janr_ro_yxat_matn(janr: str, jami: int) -> str:
    label = await _janr_label(janr)
    return (
        f"📚 <b>{x(label)}</b> — jami <b>{jami}</b> ta kitob.\n\n"
        f"Kitob nomini bosing, batafsil ma'lumot chiqadi:\n"
        f"◀️ / ▶️ tugmalari bilan varaqlang."
    )


@router.callback_query(F.data == "janrlar")
async def janrlarga_qaytish(callback: CallbackQuery):
    try:
        janrlar = await api.kitob_janrlar()
    except ApiXato as e:
        await callback.answer(e.detail, show_alert=True)
        return
    if not janrlar:
        await xabarni_tahrirlash(callback, "Hozircha kutubxonada kitoblar yo'q.")
        await callback.answer()
        return
    await xabarni_tahrirlash(
        callback,
        KATEGORIYA_SAVOLI,
        reply_markup=janr_tugmalari(janrlar),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("janr:"))
async def kategoriya_tanlandi(callback: CallbackQuery):
    janr = callback.data.split(":", 1)[1]

    try:
        kitoblar, jami = await _janr_sahifa_kitoblari(janr, sahifa=1)
    except ApiXato as e:
        await callback.answer(e.detail, show_alert=True)
        return

    if not kitoblar:
        await xabarni_tahrirlash(callback, "Bu kategoriyada kitob topilmadi.")
        await callback.answer()
        return

    matn = await _janr_ro_yxat_matn(janr, jami)
    await xabarni_tahrirlash(
        callback,
        matn,
        reply_markup=janr_kitob_tugmalari(
            janr,
            kitoblar,
            sahifa=1,
            jami=jami,
            qator_soni=JANR_QATOR_SONI,
            qatorlar_soni=JANR_QATORLAR,
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("jpage:"))
async def janr_sahifasi(callback: CallbackQuery):
    # "jpage:bosh" — sahifa ko'rsatkichi, hech narsa qilmaydi.
    if callback.data == "jpage:bosh":
        await callback.answer()
        return

    qismlar = callback.data.split(":", 2)
    if len(qismlar) < 3 or not qismlar[2].isdigit():
        await callback.answer("Sahifa raqami noto'g'ri.", show_alert=True)
        return
    janr = qismlar[1]
    sahifa = int(qismlar[2])

    try:
        kitoblar, jami = await _janr_sahifa_kitoblari(janr, sahifa=sahifa)
    except ApiXato as e:
        await callback.answer(e.detail, show_alert=True)
        return

    if not kitoblar:
        await callback.answer("Bu sahifada kitob yo'q.", show_alert=True)
        return

    matn = await _janr_ro_yxat_matn(janr, jami)
    await xabarni_tahrirlash(
        callback,
        matn,
        reply_markup=janr_kitob_tugmalari(
            janr,
            kitoblar,
            sahifa=sahifa,
            jami=jami,
            qator_soni=JANR_QATOR_SONI,
            qatorlar_soni=JANR_QATORLAR,
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("jbook:"))
async def janr_kitob_tanlandi(callback: CallbackQuery):
    qismlar = callback.data.split(":")
    if len(qismlar) < 4 or not qismlar[3].isdigit():
        await callback.answer("Kitob topilmadi.", show_alert=True)
        return
    janr, sahifa = qismlar[1], qismlar[2]
    kitob_id = int(qismlar[3])

    try:
        kitob = await api.kitob_detail(kitob_id)
    except ApiXato as e:
        await callback.answer(e.detail, show_alert=True)
        return

    matn = _kitob_batafsil_matn(kitob)
    await xabarni_tahrirlash(
        callback,
        matn,
        reply_markup=kitob_band_qilish_tugmalari(
            kitob_id,
            qaytish=f"jpage:{janr}:{sahifa}",
            navbat_mavjud=_navbat_mavjud(kitob),
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("kitob:"))
async def kitob_kartochka(callback: CallbackQuery):
    qismlar = callback.data.split(":")
    if len(qismlar) < 2 or not qismlar[1].isdigit():
        await callback.answer("Kitob topilmadi.", show_alert=True)
        return
    kitob_id = int(qismlar[1])

    try:
        kitob = await api.kitob_detail(kitob_id)
    except ApiXato as e:
        await callback.answer(e.detail, show_alert=True)
        return

    if callback.message is None:
        await callback.answer("Xabar eskirgan. Qayta qidiring.", show_alert=True)
        return

    matn = _kitob_batafsil_matn(kitob)
    await callback.message.answer(
        matn,
        reply_markup=kitob_band_qilish_tugmalari(
            kitob_id, navbat_mavjud=_navbat_mavjud(kitob)
        ),
    )
    await callback.answer()


def _mavjud_nusxa_bormi(kitob: dict) -> bool:
    """Kitobning kamida bitta `mavjud` nusxasi bormi."""
    return any(n.get("holati") == "mavjud" for n in kitob.get("nusxalar") or [])


def _navbat_mavjud(kitob: dict) -> bool:
    """«Navbatga turish» tugmasi ko'rsatilishi kerakmi?

    Faqat nusxasi bor, lekin hozir hech qanday mavjud nusxasi yo'q kitoblar
    uchun. Nusxasi umuman yo'q («asli») kitoblarda navbatga turish kitobni
    darhol berar edi, bunday kitoblar uchun faqat «Band qilish» ko'rsatiladi."""
    if not (kitob.get("nusxalar") or []):
        return False
    return not _mavjud_nusxa_bormi(kitob)


def _kitob_batafsil_matn(kitob: dict) -> str:
    """Kitob kartochkasi matni — batafsil ma'lumot + nusxa/asil holati."""
    nusxalar = kitob.get("nusxalar") or []
    mavjud_nusxa = next((n for n in nusxalar if n.get("holati") == "mavjud"), None)

    matn = (
        f"📖 <b>{x(kitob.get('nomi'))}</b>\n"
        f"Muallif: {x(kitob.get('muallif'))}\n"
        f"Janr: {x(kitob.get('janr'))}\n"
        f"Nashriyot: {x(kitob.get('nashriyot')) or '-'} "
        f"({x(kitob.get('nashr_yili'))})"
    )
    if kitob.get("tavsif"):
        matn += f"\n\n{x(kitob['tavsif'])}"

    jami = len(nusxalar)
    if mavjud_nusxa:
        javon = x(mavjud_nusxa.get("javon")) or "kutubxonachidan so'rang"
        matn += f"\n\n✅ Kitob mavjud. Kutubxonaga kelib oling (javon: {javon})."
    elif jami:
        matn += "\n\n❌ Hozircha mavjud nusxa yo'q."
    else:
        matn += (
            "\n\n⚠️ Bu kitobning kutubxonada nusxasi yo'q, "
            "asil kitobni band qilishingiz mumkin."
        )

    matn += (
        "\n\n<b>Band qilish</b> — kitobni maxsus maqsadga saqlab qoyish"
        " (o'qituvchi darsga, o'quvchi imtihonga tayyorlanmoqda). "
        "Band qilingan kitob boshqalarga berilmaydi: uni faqat kutubxonachi "
        "tasdiqlagandan keyin sizga beriladi va tasdiqlanganligi xabar qilinadi."
    )
    # Navbat faqat nusxasi bor, lekin hozir berilmaydigan kitoblar uchun.
    # Nusxasi umuman yo'q kitobda navbatga turish kitobni darhol berar edi,
    # shuning uchun u yerda ko'rsatilmaydi.
    if _navbat_mavjud(kitob):
        matn += (
            "\n\n⏳ <b>Navbatga turish</b> — hozir berish mumkin bo'lmagan kitob "
            "kutmoqchi bo'lsangiz (avval berilgach sizga taklif yuboriladi)."
        )
    return matn


@router.callback_query(F.data.startswith("band:"))
async def band_qilish_sorovi(callback: CallbackQuery):
    """«Band qilish» — kitobni tasdiqlash kutilayotgan holda saqlab qo'yish.

    So'rov yaratilgach kitobni hech kimga berib bo'lmaydi; tasdiqlashni
    kutubxonachi qiladi va shunda kitob so'rov qilgan o'quvchiga beriladi.
    """
    qismlar = callback.data.split(":")
    if len(qismlar) < 2 or not qismlar[1].isdigit():
        await callback.answer("Kitob topilmadi.", show_alert=True)
        return
    kitob_id = int(qismlar[1])

    if callback.message is None:
        await callback.answer("Xabar eskirgan. Qayta qidiring.", show_alert=True)
        return

    try:
        band = await api.band_qil(kitob_id, callback.from_user.id)
    except ApiXato as e:
        await callback.message.answer(x(BAND_XATOLARI.get(e.kod, e.detail)))
        await callback.answer()
        return

    nomi = band.get("kitob_nomi") or await _kitob_nomi(kitob_id)
    izoh = band.get("izoh")
    band_id = band.get("id")

    await callback.message.answer(
        f"{b.logo(sarlavha='BAND QILINDI')}\n\n"
        f"{b.sarlavha(x(nomi))}\n"
        + (f"<i>{x(izoh)}</i>\n" if izoh else "")
        + "So'rov yuborildi.\n\n"
        "Kutubxonachi tasdiqlagach kitobni hech kimga berilmaydi va sizga "
        "ham berilmaydi. Tasdiqlanganligi xabar qilinadi.",
        # Server javobda `id` qaytarmasa, bekor tugmasi kerak emas —
        # `/bandlarim` orqali so'rovni ko'rib, u yerda bekor qilish mumkin.
        reply_markup=band_bekor_tugmasi(band_id) if band_id else None,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("band_bekor:"))
async def band_bekor_qilish(callback: CallbackQuery):
    """O'quvchi o'z band so'rovini bekor qiladi — kitob yana ochiq bo'ladi."""
    qismlar = callback.data.split(":")
    if len(qismlar) < 2 or not qismlar[1].isdigit():
        await callback.answer("So'rov topilmadi.", show_alert=True)
        return

    try:
        await api.band_bekor_qil(int(qismlar[1]), callback.from_user.id)
    except ApiXato as e:
        await callback.answer(e.detail, show_alert=True)
        return

    await xabarni_tahrirlash(
        callback,
        "🚪 Band qilish bekor qilindi. Kitob yana boshqalarga ham berilishi mumkin.",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("navbat_tur:"))
async def navbatga_tur(callback: CallbackQuery):
    """ESKI xabarlardagi «Band qilish» tugmasi — endi tasdiqlanadigan band.

    Bu callback eskida «Band qilish» va «Navbatga turish» tugmalarida birga
    ishlatilardi. Navbat uchun endi alohida `navbat_qoldir:` callback'i bor,
    shuning uchun `navbat_tur:` faqat eski "Band qilish" tugmalariga qolgan
    va ularni to'g'ri ishlash uchun band so'roviga yo'naltiramiz.

    Oldin shu callback nusxasi yo'q kitobda kitobni DARHOL berar edi —
    foydalanuvchi «band qildim» deb o'ylab, kitobni olib qoldi."""
    kitob_id = await _band_kitob_idi(callback)
    if kitob_id is None:
        return
    await _band_so_rovi_yubor(callback, kitob_id)


@router.callback_query(F.data.startswith("navbat_qoldir:"))
async def navbat_qoldirish(callback: CallbackQuery):
    """«⏳ Navbatga turish» — nusxasi bor, hozir berilmaydigan kitob uchun navbat.

    Faqat navbatga o'rin oladi, kitobni hech qachon darhol bermaydi."""
    kitob_id = await _band_kitob_idi(callback)
    if kitob_id is None:
        return
    assert callback.message is not None  # `_band_kitob_idi` tekshirgan
    telegram_id = callback.from_user.id

    try:
        natija = await api.navbatga_tur(kitob_id, telegram_id)
    except ApiXato as e:
        await callback.message.answer(x(NAVBAT_XATOLARI.get(e.kod, e.detail)))
        await callback.answer()
        return

    nomi = await _kitob_nomi(kitob_id)

    if natija.get("berildi"):
        # Nusxasi bor kitob bo'shatilsa va shu zahoti navbatdagi odamga
        # berib bo'lsa. Aks holda oddiy navbat xabari ko'rsatiladi.
        berish = natija.get("berish") or {}
        muddat = berish.get("qaytarish_muddati")
        qator = f"📖 <b>{x(nomi)}</b>"
        if muddat:
            qator += f"\n📅 Qaytarish muddati: {muddat}"
        await callback.message.answer(
            f"✅ {qator}\n\nKitob navbatdan sizga berildi.\n"
            "📚 Mening kitoblarim orqali qaytarish muddatini ko'rasiz."
        )
    else:
        # `orin` serverda bo'lmasligi mumkin (natijada maydon yo'q) —
        # `KeyError` o'rniga oddiy "navbatdasiz" yoziladi.
        orin = natija.get("orin")
        o_rin = f"{orin}-o'rindasiz" if orin else "navbatdasiz"
        await callback.message.answer(
            f"<b>Navbatga qo'shildingiz!</b> Siz {o_rin}.\n\n"
            f"Kitob bo'shagan zahoti «{x(nomi)}» kitobini sizga taklif qilinadi. "
            "Navbatni bekor qilish uchun «Navbatlarim» bo'limidan foydalaning.\n"
            "Maxsus maqsadga (dars, imtihon, tadbir) ajratish uchun esa "
            "«Band qilish»ni ishlating — u tasdiqlash kutiladi."
        )
    await callback.answer()


async def _band_kitob_idi(callback: CallbackQuery) -> int | None:
    """Callback ma'lumotidan kitob ID sini oladi (xabar eskirgan bo'lsa None)."""
    qismlar = callback.data.split(":")
    if len(qismlar) < 2 or not qismlar[1].isdigit():
        await callback.answer("Kitob topilmadi.", show_alert=True)
        return None
    if callback.message is None:
        await callback.answer("Xabar eskirgan. Qayta qidiring.", show_alert=True)
        return None
    return int(qismlar[1])


async def _band_so_rovi_yubor(callback: CallbackQuery, kitob_id: int) -> None:
    """Tasdiqlanadigan band so'rovini yaratadi (Berish yozuvi OCHILMAYDI)."""
    try:
        band = await api.band_qil(kitob_id, callback.from_user.id)
    except ApiXato as e:
        await callback.message.answer(x(BAND_XATOLARI.get(e.kod, e.detail)))
        await callback.answer()
        return

    nomi = band.get("kitob_nomi") or await _kitob_nomi(kitob_id)
    band_id = band.get("id")
    await callback.message.answer(
        f"{b.logo(sarlavha='BAND QILINDI')}\n\n"
        f"{b.sarlavha(x(nomi))}\n"
        "So'rov yuborildi.\n\n"
        "Kutubxonachi tasdiqlagach kitobni hech kimga berilmaydi va sizga "
        "ham berilmaydi. Tasdiqlanganligi xabar qilinadi.",
        reply_markup=band_bekor_tugmasi(band_id) if band_id else None,
    )
    await callback.answer()


async def _kitob_nomi(kitob_id: int) -> str:
    try:
        kitob = await api.kitob_detail(kitob_id)
        return kitob.get("nomi", "kitob")
    except Exception:
        return "kitob"