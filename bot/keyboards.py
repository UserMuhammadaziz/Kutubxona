import re

from aiogram.types import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

KITOB_QIDIRISH = "🔍 Kitob qidirish"
KATEGORIYALAR = "📚 Kategoriyalar"
MENING_KITOBLARIM = "📚 Mening kitoblarim"
NAVBATLARIM = "⏳ Navbatlarim"
BANDLARIM = "🔖 Bandlarim"
JARIMALARIM = "💰 Jarimalarim"
TELEFON_YUBORISH = "📱 Telefon raqamni yuborish"

MENYU_YORDAM = "❓ Yordam"

# Pastdigi KATTA tugmalar (ReplyKeyboardMarkup) — botning asosiy menyusi.
# Ularning matni shu o'zgaruvchilardan olinadi: `handlers/qidiruv.py`,
# `handlers/shaxsiy.py` va `handlers/navigatsiya.py` shu matnlarni filtr
# sifatida ishlatadi (`F.text == KITOB_QIDIRISH`).
#
# `ASOSIY_TUGMALAR` shu matnlar to'plamidir. U ikki joyda himoya uchun
# ishlatiladi: ariza bosqichida foydalanuvchi menyu tugmasini bosib, uni
# maydonga yozib yubormasligi kerak (`start.py::_menyu_tugmasi_bosilganmi`),
# `kutubxonachi.py` esa inventar raqami o'rniga kelganini tekshiradi.
ASOSIY_TUGMALAR = frozenset(
    {
        KITOB_QIDIRISH,
        KATEGORIYALAR,
        MENING_KITOBLARIM,
        NAVBATLARIM,
        BANDLARIM,
        JARIMALARIM,
        MENYU_YORDAM,
    }
)

def menyu_tugmalari() -> InlineKeyboardMarkup:
    """Yordam tugmasi — xabar ichida (inline)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=MENYU_YORDAM, callback_data="menyu:yordam")]
        ]
    )


def asosiy_tugmalar_klaviaturasi() -> ReplyKeyboardMarkup:
    """Asosiy menyu — xabar yozish maydonining OSTIDAGI katta tugmalar.

    Bu Telegram'da eng ko'p bosiladigan joy, shuning uchun bo'limlar shu
    yerga qo'yildi. Avval ular «Menu» tugmasi orqali ochiladigan inline
    tugmalar edi — uch bosish talab qilardi.

    `Yordam` tugmasi oxirgi qatorda, keng (to'liq qator) — u boshqa
    bo'limlardan farqli qaror (yordam so'rash), shuning uchun ajratilgan.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=KITOB_QIDIRISH), KeyboardButton(text=KATEGORIYALAR)],
            [
                KeyboardButton(text=MENING_KITOBLARIM),
                KeyboardButton(text=NAVBATLARIM),
            ],
            [KeyboardButton(text=BANDLARIM), KeyboardButton(text=JARIMALARIM)],
            [KeyboardButton(text=MENYU_YORDAM)],
        ],
        resize_keyboard=True,
    )


def telefon_sorash() -> ReplyKeyboardMarkup:
    """Telefon bosqichida kontakt yuborish tugmasi.

    Bu menyu tugmasi EMAS — foydalanuvchi telefon raqamini qo'lda yozish
    o'rniga bir tush bilan yuborishi uchun kerak. Raqam qabul qilingach
    klaviatura `ReplyKeyboardRemove` bilan olib tashlanadi.
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=TELEFON_YUBORISH, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def klaviatura_olib_tashla() -> ReplyKeyboardRemove:
    """Pastdagi klaviaturani butunlay yo'q qiladi.

    Telefon bosqichida `telefon_sorash()` klaviaturasini olib tashlash uchun
    ishlatiladi — aks holda kontakt tugmasi butun chat bo'ylab qolib ketadi.
    """
    return ReplyKeyboardRemove()


def bot_buyruglar() -> list[BotCommand]:
    """Standart Telegram «Menu» tugmasi ro'yxatidagi buyruqlar.

    Ataka faqat ikki ta: `/start` va `/yordam`. Boshqa bo'limlar uchun
    buyruqlar kerak emas — ular pastdagi katta tugmalarda (`/start` dan
    keyin chiqadi).

    Boshqa buyruqlar (`/bekor`, `/qaytar`, `/bandlar`, ...) ataka MENYU
    ro'yxatiga qo'yilmaydi, lekin `handlers/navigatsiya.py` da ishlayveradi:
    ular arrizа to'ldirilayotganda matn sifatida qabul qilinmasligi uchun
    handler'lari shu router'da BIRINCHI turadi.
    """
    return [
        BotCommand(command="start", description="Botni qayta boshlash / menyu"),
        BotCommand(command="yordam", description="Bot imkoniyatlari va buyruqlar"),
    ]


# ---------- A'rolik arizasi ----------

ARIZA_ROL_OQUVCHI = "oquvchi"
ARIZA_ROL_OQITUVCHI = "oqituvchi"

ARIZA_ROL_TUGMA_MATNLARI = {
    ARIZA_ROL_OQUVCHI: "🎓 Oquvchi sifatida a'riza yuborish",
    ARIZA_ROL_OQITUVCHI: "👨‍🏫 O'qituvchi sifatida a'riza yuborish",
}


def ariza_rol_tugmalari() -> InlineKeyboardMarkup:
    """/start da ariza yuboruvchi rolini tanlaydigan inline tugmalar."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ARIZA_ROL_TUGMA_MATNLARI[ARIZA_ROL_OQUVCHI],
                    callback_data=f"ariza_rol:{ARIZA_ROL_OQUVCHI}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=ARIZA_ROL_TUGMA_MATNLARI[ARIZA_ROL_OQITUVCHI],
                    callback_data=f"ariza_rol:{ARIZA_ROL_OQITUVCHI}",
                )
            ],
        ]
    )


def telefon_keltirish(raw: str) -> str | None:
    """Raqamni `+998XXXXXXXXX` ko'rinishiga keltiradi, imkonsiz bo'lsa None.

    Qabul qilinadigan yozuvlar: `+998901234567`, `998901234567`,
    `+998 90 123 45 67`, `+998-90-123-45-67`, `00998901234567`, `901234567` (998 yozilmasdan).
    Bo'sh joy, chiziqcha va qavs ( ) olib tashlanadi.
    """
    if not raw:
        return None
    raqamlar = re.sub(r"\D", "", raw)
    if raqamlar.startswith("00998"):
        raqamlar = "998" + raqamlar[5:]
    if raqamlar.startswith("998"):
        yakuniy = "+" + raqamlar
    elif raqamlar.startswith("9") and len(raqamlar) == 9:
        # Raqam 998 yozilmasdan kelgan bo'lsa (masalan "901234567").
        yakuniy = "+998" + raqamlar
    else:
        return None
    # "+998" (4 belgi) + 9 ta raqam = 13 belgi — backend validatori bilan bir xil.
    return yakuniy if re.fullmatch(r"\+998\d{9}", yakuniy) else None


def matndan_telefon_keltirish(text: str) -> str | None:
    """Matn ichidan telefon raqamini ajratib oladi (asosiy usul Telegram Contact)."""
    if not text or TELEFON_YUBORISH in text:
        return None
    for candidat in re.findall(r"\+?\d[\d\s\-()]{6,}", text):
        telefon = telefon_keltirish(candidat)
        if telefon:
            return telefon
    return None


def kitob_batafsil_tugmasi(kitob_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ℹ️ Batafsil", callback_data=f"kitob:{kitob_id}")]
        ]
    )


def janr_tugmalari(janrlar: list[dict], qator_soni: int = 2) -> InlineKeyboardMarkup:
    """Janrlar bo'yicha inline tugmalar (qatorida qator_soni dan tugma)."""
    tugmalar = [
        InlineKeyboardButton(
            text=f"📖 {j['label']} ({j['soni']})",
            callback_data=f"janr:{j['key']}",
        )
        for j in janrlar
    ]
    qatorlar = [
        tugmalar[i : i + qator_soni] for i in range(0, len(tugmalar), qator_soni)
    ]
    return InlineKeyboardMarkup(inline_keyboard=qatorlar)


JANR_ORQAGA = "🔙 Janrlar"


def janr_kitob_tugmalari(
    janr: str,
    kitoblar: list[dict],
    sahifa: int,
    jami: int,
    qator_soni: int = 1,
    qatorlar_soni: int = 10,
) -> InlineKeyboardMarkup:
    """Tanlangan janrdagi kitoblar: bittadan (qator_soni=1), bo'yiga qatorlar_soni
    (10) tasi — bitta ekranda 10 tagacha kitob nomi inline tugma, nomi to'liq
    ko'rinadi. Yoniga o'tish (◀️ Oldingi / Keyingi ▶️) tugmalari orqali janrdagi
    hamma kitobni varaqlash mumkin (jami jami ta)."""

    ko_rsatiladi = kitoblar[: qator_soni * qatorlar_soni]
    tugmachalar = []
    for k in ko_rsatiladi:
        nomi = k["nomi"]
        matn = nomi if len(nomi) <= 60 else f"{nomi[:59]}…"
        tugmachalar.append(
            InlineKeyboardButton(
                text=f"📖 {matn}",
                callback_data=f"jbook:{janr}:{sahifa}:{k['id']}",
            )
        )

    qatorlar = [
        tugmachalar[i : i + qator_soni]
        for i in range(0, len(tugmachalar), qator_soni)
    ]

    jami_sahifalar = max(1, -(-jami // (qator_soni * qatorlar_soni)))
    nav = []
    if sahifa > 1:
        nav.append(
            InlineKeyboardButton(
                text="◀️ Oldingi", callback_data=f"jpage:{janr}:{sahifa - 1}"
            )
        )
    nav.append(
        InlineKeyboardButton(text=f"{sahifa} / {jami_sahifalar}", callback_data="jpage:bosh")
    )
    if sahifa < jami_sahifalar:
        nav.append(
            InlineKeyboardButton(
                text="Keyingi ▶️", callback_data=f"jpage:{janr}:{sahifa + 1}"
            )
        )
    qatorlar.append(nav)
    qatorlar.append([InlineKeyboardButton(text=JANR_ORQAGA, callback_data="janrlar")])
    return InlineKeyboardMarkup(inline_keyboard=qatorlar)


def kitob_band_qilish_tugmalari(
    kitob_id: int, qaytish: str | None = None, navbat_mavjud: bool = False
) -> InlineKeyboardMarkup:
    """Batafsil sahifada: kitobni band qilish (tasdiqlanadi) + navbat.

    * `🔒 Band qilish` — kitobni maxsus maqsadga saqlab qo'yish so'rovi.
      So'rov yaratilgach kitob **hech kimga berilmaydi**; faqat kutubxonachi
      yoki administrator tasdiqlagandan keyin so'rov qilgan o'quvchiga
      beriladi.
    * `⏳ Navbatga turish` — mavjud nusxa yo'q bo'lganda oddiy navbat.
    """
    inline_keyboard = [
        [InlineKeyboardButton(text="🔒 Band qilish", callback_data=f"band:{kitob_id}")]
    ]
    if navbat_mavjud:
        inline_keyboard.append(
            [InlineKeyboardButton(text="⏳ Navbatga turish", callback_data=f"navbat_qoldir:{kitob_id}")]
        )
    if qaytish:
        inline_keyboard.append(
            [InlineKeyboardButton(text="🔙 Ro'yxatga qaytish", callback_data=qaytish)]
        )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def band_bekor_tugmasi(band_id: int) -> InlineKeyboardMarkup:
    """Mening bandlarim: kutilayotgan so'rovni bekor qilish.

    Tugma matni qisqa va yagona uslubda («Bekor qilish») — avvalgi
    «🚪 Bandni bekor qilish» emoji bilan aralashib, tor ekranda
    chiroqsiz ko'rinardi."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Bekor qilish", callback_data=f"band_bekor:{band_id}")]
        ]
    )


def band_tasdiq_tugmalari(band_id: int) -> InlineKeyboardMarkup:
    """Kutubxonachi: band so'rovini tasdiqlash yoki rad etish.

    Ikki tugma bir qatorda, matnlari teng uzunligida («Tasdiqlash» /
    «Rad etish») — shaklda bir xil ko'rinadi. `Tasdiqlash` kitobni
    o'quvchiga berishni bildiradi, shuning uchun `(berish)` kabi
    uzun qo'shimcha olib tashlandi (batafsil matn xabarda bor)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Tasdiqlash", callback_data=f"band_tasdiq:{band_id}"),
                InlineKeyboardButton(text="Rad etish", callback_data=f"band_rad:{band_id}"),
            ]
        ]
    )


def navbatga_turish_tugmasi(kitob_id: int) -> InlineKeyboardMarkup:
    """«⏳ Navbatga turish» — navbat uchun **alohida** `navbat_qoldir:` callback'i.

    Eski `navbat_tur:` callback'i «Band qilish» tugmasi bilan bir bo'lib,
    eski xabarlarda band so'rovi sifatida ishlaydi. Navbat uchun boshqa
    nom ishlatiladi, shunda eski va yangi tugmalar chalkashmaydi."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏳ Navbatga turish", callback_data=f"navbat_qoldir:{kitob_id}")]
        ]
    )


def taklif_javob_tugmalari(navbat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Olaman", callback_data=f"navbat_javob:{navbat_id}:olaman"),
                InlineKeyboardButton(text="❌ Kerak emas", callback_data=f"navbat_javob:{navbat_id}:kerak_emas"),
            ]
        ]
    )


def navbatdan_chiqish_tugmasi(navbat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚪 Navbatdan chiqish", callback_data=f"navbat_chiq:{navbat_id}")]
        ]
    )


def qaytarish_tasdiq_tugmasi(berish_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Qaytarib olish", callback_data=f"qaytar:{berish_id}")]
        ]
    )