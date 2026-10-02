"""O'quvchi moduli uchun biznes logikasi va Telegram xabarlari.

Arizani tasdiqlash / rad etish jarayonida o'quvchiga yuboriladigan xabarlar
shu yerda yig'iladi — API view va Django admin bir xil matndan foydalanadi
(aks holda ikki xabardan biri eslab qolinib qolardi).
"""
from datetime import date

from django.db import IntegrityError, transaction
from django.utils.timezone import now

from config.telegram import telegram_escape, telegram_xabar_yubor
from .models import Ariza, Oquvchi

# Karta raqami unique bo'lgani uchun ikki so'rov bir vaqtda yuborilsa
# bir xil raqam olinishi mumkin. Bunday holda IntegrityError keladi va
# biz keyingi raqam bilan qayta urinamiz.
_KARTA_URINISH_SONI = 5


def keyingi_karta_raqami() -> str:
    """LIB-{yil}-{4 xonali tartib raqam} formatida keyingi bo'sh raqam."""
    prefiks = f"LIB-{date.today().year}-"
    oxirgi = (
        Oquvchi.objects.filter(karta_raqami__startswith=prefiks)
        .order_by("-karta_raqami")
        .first()
    )
    if oxirgi:
        try:
            tartib = int(oxirgi.karta_raqami.split("-")[-1]) + 1
        except ValueError:
            tartib = 1
    else:
        tartib = 1
    return f"{prefiks}{tartib:04d}"


def oquvchi_yarat(**maydonlar) -> Oquvchi:
    """Karta raqamini avtomatik to'ldirib yangi o'quvchi yaratadi.

    Karta raqami generatsiyasi «eng katta raqam + 1» tamoyiliga asoslangan
    bo'lgani uchun parallel so'rovlarda bir to'qnashuv bo'lishi mumkin.
    Shu sababli IntegrityError yuzaga kelsa, saqovli (savepoint) ichida
    qayta urinib, keyingi raqam bilan yana urinishadi. Boshqa sababli
    xatolar (masalan, takrorlanuvchi telefon) o'zgarishsiz qaytariladi.
    """
    for _ in range(_KARTA_URINISH_SONI):
        try:
            with transaction.atomic():
                return Oquvchi.objects.create(
                    karta_raqami=keyingi_karta_raqami(), **maydonlar
                )
        except IntegrityError as xato:
            karta_urindi = "karta_raqami" in str(xato)
            if not karta_urindi:
                raise
    raise IntegrityError(
        "Karta raqamini generatsiya qilishda takroriy urinishlar muvaffaqiyatsiz bo'ldi"
    )


class ArizaTelegramBandi(ValueError):
    """Ariza berilgan telefon raqami boshqa telegram akkauntga bog'langan."""

    def __init__(self, ariza: Ariza):
        self.ariza = ariza
        super().__init__(
            "Bu telefon raqami allaqachon boshqa telegram akkauntga bog'langan"
        )


def tasdiqlash_xabari(ariza: Ariza, oquvchi: Oquvchi, yangi_karta: bool) -> str:
    """Ariza qabul qilinganda arizani yuborgan shaxsga yuboriladigan xabar matni."""
    fish = telegram_escape(oquvchi.fish)
    karta = telegram_escape(oquvchi.karta_raqami)
    if ariza.rol == "oqituvchi":
        sinf_qismi = ""
        kasb_qismi = f"\n📚 Kasbingiz: <b>{telegram_escape(ariza.kasb)}</b>" if ariza.kasb else ""
    else:
        sinf_qismi = (
            f"\n🎓 Sinf: <b>{telegram_escape(oquvchi.sinf)}</b>" if oquvchi.sinf else ""
        )
        kasb_qismi = ""
    karta_qismi = (
        f"\n🆕 Sizga berilgan karta raqami: <b>{karta}</b>\n"
        "Bu raqamni saqlab qo'ying." if yangi_karta else ""
    )
    return (
        "✅ <b>A'zolik arizangiz tasdiqlandi!</b>\n\n"
        f"Xush kelibsiz, {fish}!"
        f"{sinf_qismi}{kasb_qismi}\n"
        f"🪪 Karta raqamingiz: <b>{karta}</b>"
        f"{karta_qismi}\n\n"
        "Endi /start buyrug'ini bosing va kitob qidirish, navbatga turish, "
        "jarimalarni ko'rish imkoniyatlaridan foydalaning."
    )


def rad_etilgan_xabari(ariza: Ariza, izoh: str) -> str:
    """Ariza rad etilganda o'quvchiga yuboriladigan xabar matni."""
    izoh_qismi = f"\n\n📝 Sabab: <b>{telegram_escape(izoh)}</b>" if izoh else ""
    return (
        "❌ <b>A'zolik arizangiz rad etildi.</b>\n\n"
        "Buning sabablarini quyidagilar bo'lishi mumkin:\n"
        "• Ro'yxatga olish shartlari bajarilmagan\n"
        "• Telefon raqamingiz noto'g'ri kiritilgan\n"
        "• Hujjatlar to'liq emas\n"
        f"{izoh_qismi}\n\n"
        "Batafsil ma'lumot uchun kutubxonaga murojaat qiling. "
        "Takror urinib ko'rsangiz, arizangizni qayta yubora olasiz."
    )


def ariza_holatini_yubor(ariza: Ariza, matn: str) -> bool:
    """Ariza bo'yicha xabarni Telegram orqali yuboradi.

    Transaction ichidan chaqirilganda `on_commit` ga qo'yiladi — ya'ni
    ma'lumot bazasi muvaffaqiyatli yozilgandan keyingina yuboriladi va
    bekor qilingan tranzaksiyadan keyin xabar ketmaydi.
    """
    telegram_id = ariza.telegram_id
    if not telegram_id:
        return False
    transaction.on_commit(lambda: telegram_xabar_yubor(telegram_id, matn))
    return True


def arizani_tasdiqla(ariza: Ariza):
    """Arizani tasdiqlaydi: o'quvchi mavjud bo'lsa yangilanadi, yo'qsa
    yangi o'quvchi karta raqami bilan yaratiladi. (ariza, oquvchi, yangi_karta)

    Eslatma: mavjud o'quvchining `telegram_id` si boshqa akkauntga tegishli
    bo'lsa, bu ariza rad etiladi (`ArikaTelegramBandi` xatosi) — aks holda
    birinchi o'quvchining akkaunti ikkinchisining arizasi orqali
    almashtirilib qolardi.
    """
    if ariza.holati != "kutmoqda":
        raise ValueError("Faqat 'kutmoqda' holatidagi ariza tasdiqlanadi")

    oquvchi = Oquvchi.objects.filter(telefon=ariza.telefon).first()
    yangi_karta = oquvchi is None

    if oquvchi:
        if oquvchi.telegram_id and oquvchi.telegram_id != ariza.telegram_id:
            raise ArizaTelegramBandi(ariza)
        oquvchi.telegram_id = ariza.telegram_id
        oquvchi.fish = ariza.fish
        # Sinf, tugilgan_sana va manzil arizadagi qiymat bilan to'ldiriladi,
        # lekin o'quvchi ularni allaqachon to'ldirgan bo'lsa ustidan
        # yozilmaydi (ariza ko'pincha faqat ism/telefon/sinf so'raydi).
        # Faqat o'zgarishi kerak bo'lgan maydonlarni saqlaymiz.
        yangilangan = ["telegram_id", "fish"]
        if oquvchi.sinf != ariza.sinf and ariza.sinf:
            oquvchi.sinf = ariza.sinf
            yangilangan.append("sinf")
        if ariza.tugilgan_sana and not oquvchi.tugilgan_sana:
            oquvchi.tugilgan_sana = ariza.tugilgan_sana
            yangilangan.append("tugilgan_sana")
        if ariza.manzil and not oquvchi.manzil:
            oquvchi.manzil = ariza.manzil
            yangilangan.append("manzil")
        oquvchi.save(update_fields=yangilangan)
    else:
        oquvchi = oquvchi_yarat(
            fish=ariza.fish,
            telefon=ariza.telefon,
            telegram_id=ariza.telegram_id,
            sinf=ariza.sinf or "",
            tugilgan_sana=ariza.tugilgan_sana,
            manzil=ariza.manzil,
        )

    ariza.holati = "tasdiqlandi"
    ariza.tasdiqlangan_sana = now()
    ariza.save(update_fields=["holati", "tasdiqlangan_sana"])
    return ariza, oquvchi, yangi_karta


def arizani_rad_et(ariza: Ariza, izoh: str = ""):
    """Arizani rad etadi va izohni saqlaydi."""
    if ariza.holati != "kutmoqda":
        raise ValueError("Faqat 'kutmoqda' holatidagi ariza rad etiladi")
    ariza.holati = "bekor"
    ariza.izoh = (izoh or "")[:255]
    ariza.save(update_fields=["holati", "izoh"])
    return ariza
