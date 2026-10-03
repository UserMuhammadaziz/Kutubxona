from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api_client import ApiXato, api
from keyboards import (
    KATEGORIYALAR,
    KITOB_QIDIRISH,
    band_bekor_tugmasi,
    janr_kitob_tugmalari,
    janr_tugmalari,
    kitob_batafsil_tugmasi,
    kitob_band_qilish_tugmalari,
    navbatga_turish_tugmasi,
)
from states import Qidiruv
from utils import x, xabarni_tahrirlash

router = Router(name="qidiruv")

KO_RSATILADIGAN_SONI = 10

# Janr sahifasi: bitta tugma bir qatorda, bo'yiga 10 tasi — bir ekranda 10 ta kitob.
JANR_QATOR_SONI = 1
JANR_QATORLAR = 10
# Server /api/books/ PARK sahifasida 20 ta kitob qaytaradi (config/settings.py PAGE_SIZE).
JANR_API_SAHIFA_O_LCHAMI = 20

_janr_label_lar = {}


async def _janr_label(janr_key: str) -> str:
    """Janr kalitini chiroyli nomiga aylantiradi (genres API dan, bir marta)."""
    if janr_key not in _janr_label_lar:
        try:
            janrlar = await api.kitob_janrlar()
            _janr_label_lar.update({j["key"]: j["label"] for j in janrlar})
        except Exception:
            pass
    return _janr_label_lar.get(janr_key, janr_key)


async def _janr_sahifa_kitoblari(janr: str, sahifa: int):
    """sahifa (10 tadan) ni API sahifasi/offset ga moslab olib qaytaradi.
    Kitoblarni birdaniga 20 tadan qaytaradigan API'dan 10 tadan ko'rsatish
    uchun kerak bo'lgan sahifani hisoblaydi."""
    nisbat = JANR_API_SAHIFA_O_LCHAMI // JANR_QATORLAR  # 20 // 10 = 2
    api_sahifa = (sahifa - 1) // nisbat + 1
    boshi = ((sahifa - 1) % nisbat) * JANR_QATORLAR
    kitoblar, jami = await api.kitoblar_janr_boicha(janr, page=api_sahifa)
    return kitoblar[boshi : boshi + JANR_QATORLAR], jami


@router.message(F.text == KITOB_QIDIRISH)
async def qidiruv_boshla(message: Message, state: FSMContext):
    await state.set_state(Qidiruv.matn)
    await message.answer("Kitob nomi, muallif yoki ISBN ni yozing:")


@router.message(Qidiruv.matn)
async def qidiruv_natija(message: Message, state: FSMContext):
    await state.clear()
    q = (message.text or "").strip()
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
            f"📖 <b>{x(kitob['nomi'])}</b> — {x(kitob['muallif'])} ({x(kitob['nashr_yili'])})\n"
            f"Mavjud: {kitob['mavjud_nusxalar']} / {kitob['jami_nusxalar']}"
        )
        await message.answer(matn, reply_markup=kitob_batafsil_tugmasi(kitob["id"]))

    if len(natijalar) > KO_RSATILADIGAN_SONI:
        await message.answer(
            f"Jami {len(natijalar)} ta natija topildi. Aniqroq so'rov bilan qayta izlang."
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

    await message.answer(
        "📚 Kategoriyani tanlang:",
        reply_markup=janr_tugmalari(janrlar),
    )


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
        "📚 Kategoriyani tanlang:",
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
            navbat_mavjud=not _mavjud_nusxa_bormi(kitob),
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
            kitob_id, navbat_mavjud=not _mavjud_nusxa_bormi(kitob)
        ),
    )
    await callback.answer()


def _mavjud_nusxa_bormi(kitob: dict) -> bool:
    """Kitobning kamida bitta `mavjud` nusxasi bormi."""
    return any(n.get("holati") == "mavjud" for n in kitob.get("nusxalar") or [])


def _kitob_batafsil_matn(kitob: dict) -> str:
    """Kitob kartochkasi matni — batafsil ma'lumot + nusxa/asil holati."""
    mavjud_nusxa = next((n for n in kitob["nusxalar"] if n["holati"] == "mavjud"), None)

    matn = (
        f"📖 <b>{x(kitob['nomi'])}</b>\n"
        f"Muallif: {x(kitob['muallif'])}\n"
        f"Janr: {x(kitob['janr'])}\n"
        f"Nashriyot: {x(kitob.get('nashriyot')) or '-'} ({x(kitob['nashr_yili'])})"
    )
    if kitob.get("tavsif"):
        matn += f"\n\n{x(kitob['tavsif'])}"

    jami = len(kitob["nusxalar"])
    if mavjud_nusxa:
        javon = x(mavjud_nusxa.get("javon")) or "kutubxonachidan so'rang"
        matn += f"\n\n✅ Kitob mavjud. Kutubxonaga kelib oling (javon: {javon})."
    elif jami:
        matn += "\n\n❌ Hozircha mavjud nusxa yo'q."
    else:
        matn += "\n\n⚠️ Bu kitobning kutubxonada nusxasi yo'q, asil kitobni band qilishingiz mumkin."

    matn += (
        "\n\n🔒 <b>Band qilish</b> — kitobni maxsus maqsadga saqlab qoyish"
        " (o'qituvchi darsga tayyorlanmoqda, o'quvchi imtihonga...). "
        "Band qilingan kitob boshqalarga berilmaydi: uni faqat kutubxonachi "
        "yoki administrator tasdiqlagandan keyin sizga beriladi."
    )
    if not mavjud_nusxa:
        matn += (
            "\n\n⏳ <b>Navbatga turish</b> — hozir berish mumkin bo'lmagan kitob "
            "kutmoqchi bo'lsangiz (avval berilgach sizga taklif yuboriladi)."
        )
    return matn


@router.callback_query(F.data.startswith("band:"))
async def band_qilish_sorovi(callback: CallbackQuery):
    """«🔒 Band qilish» — kitobni tasdiqlash kutilayotgan holda saqlab qo'yish.

    So'rov yaratilgach kitobni hech kimga berib bo'lmaydi; tasdiqlashni
    kutubxonachi yoki administrator qiladi va shunda kitob so'rov qilgan
    o'quvchiga beriladi.
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
        xabarlar = {
            "oquvchi_topilmadi": "Avval /start orqali ro'yxatdan o'ting.",
            "topilmadi": "Avval /start orqali ro'yxatdan o'ting.",
            "oquvchi_bloklangan": "Sizning kartangiz bloklangan.",
            "allaqachon_band_qilingan": "Bu kitob boshqa o'quvchi uchun band qilingan.",
            "allaqachon_berilgan": "Bu kitob allaqachon sizda bor.",
        }
        await callback.message.answer(x(xabarlar.get(e.kod, e.detail)))
        await callback.answer()
        return

    nomi = band.get("kitob_nomi") or await _kitob_nomi(kitob_id)
    qator = f"📖 <b>{x(nomi)}</b>"
    izoh = band.get("izoh")
    if izoh:
        qator += f"\n📝 {x(izoh)}"

    await callback.message.answer(
        f"🔒 {qator}\n\n"
        "Kitob band qilishga so'rov qilindi.\n"
        "⏳ Endi uni faqat <b>kutubxonachi yoki administrator</b> tasdiqlaydi — "
        "tasdiqlangach kitob boshqalarga ham berilmaydi.\n\n"
        "Tasdiqlanganligi xabar qilinadi. «🔒 Bandlarim» orqali holatni "
        "kuzatib turishingiz mumkin.",
        reply_markup=band_bekor_tugmasi(band["id"]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("band_bekor:"))
async def band_bekor_qilish(callback: CallbackQuery):
    """O'quvchi o'z band'so'rovini bekor qiladi — kitob yana ochiq bo'ladi."""
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
    qismlar = callback.data.split(":")
    if len(qismlar) < 2 or not qismlar[1].isdigit():
        await callback.answer("Kitob topilmadi.", show_alert=True)
        return
    kitob_id = int(qismlar[1])
    telegram_id = callback.from_user.id

    if callback.message is None:
        await callback.answer("Xabar eskirgan. Qayta qidiring.", show_alert=True)
        return

    try:
        natija = await api.navbatga_tur(kitob_id, telegram_id)
    except ApiXato as e:
        xabarlar = {
            "oquvchi_topilmadi": "Avval /start orqali ro'yxatdan o'ting.",
            "topilmadi": "Avval /start orqali ro'yxatdan o'ting.",
            "oquvchi_bloklangan": "Sizning kartangiz bloklangan.",
            "allaqachon_navbatda": "Siz bu kitobga allaqachon navbatdasiz.",
            "barcha_nusxalar_berilgan": "Bu kitobning nusxalari hozir berilgan.",
        }
        await callback.message.answer(x(xabarlar.get(e.kod, e.detail)))
        await callback.answer()
        return

    nomi = await _kitob_nomi(kitob_id)

    # Nusxasi yo'q kitobda navbatga qo'shilmaydi — asli kitob darhol
    # beriladi. Aks holda foydalanuvchi navbatda turib qolardi va
    # hech qachon kitob olmaganini sezmasdi.
    if natija.get("berildi"):
        berish = natija.get("berish") or {}
        muddat = berish.get("qaytarish_muddati")
        qator = f"📖 <b>{x(nomi)}</b>"
        if muddat:
            qator += f"\n📅 Qaytarish muddati: {muddat}"
        await callback.message.answer(
            f"✅ {qator}\n\n"
            "Kitobda nusxa yo'q edi, shuning uchun <b>asli kitob</b> sizga "
            "berildi (band qilindi).\n"
            "📚 Mening kitoblarim orqali qaytarish muddatini ko'rasiz."
        )
    else:
        await callback.message.answer(
            f"✅ Navbatga qo'shildingiz! Siz {natija['orin']}-o'rindasiz.\n\n"
            f"Kitob bo'shagan zahoti «{x(nomi)}» kitobini sizga taklif qilinadi. "
            "Navbatni bekor qilish uchun «⏳ Navbatlarim» bo'limidan foydalaning.\n"
            "💡 Maxsus maqsadga (dars, imtihon, tadbir) ajratish uchun esa "
            "«🔒 Band qilish» ni ishlating — u tasdiqlash kutiladi."
        )
    await callback.answer()


async def _kitob_nomi(kitob_id: int) -> str:
    try:
        kitob = await api.kitob_detail(kitob_id)
        return kitob.get("nomi", "kitob")
    except Exception:
        return "kitob"