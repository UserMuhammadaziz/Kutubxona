from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from config.telegram import telegram_escape, telegram_xabar_yubor
from jarima.models import Jarima
from jarima.services import jarimani_hisobla
from kitob.models import Kitob
from kitob.services import kitob_holatini_yenila
from navbat.models import Navbat
from navbat.services import keyingi_navbatga_taklif_yubor, navbatga_qosh
from nusxa.models import Nusxa
from .models import Berish


def _xato(kod, detail, **qoshimcha):
    raise ValidationError({"error": kod, "detail": detail, **qoshimcha})


def _oq_berish_cheklovlari(oquvchi):
    """Kitob berishdan oldin o'quvchi bo'yicha umumiy cheklovlar: faollik,
    bir vaqtda oladigan kitob limiti va to'lanmagan jarima."""
    if not oquvchi.faol:
        _xato("oquvchi_bloklangan", "O'quvchi bloklangan")

    faol_soni = Berish.objects.filter(oquvchi=oquvchi, qaytarilgan_sana__isnull=True).count()
    if faol_soni >= settings.LIMIT_KITOB:
        _xato("limit_oshdi", f"O'quvchida allaqachon {settings.LIMIT_KITOB} ta kitob bor")

    if Jarima.objects.filter(berish__oquvchi=oquvchi, tolandimi=False).exists():
        _xato("tolanmagan_jarima", "O'quvchida to'lanmagan jarima bor")


def faol_asli_berish(kitob_id):
    """Nusxasi yo'q kitobning «asli» holda berilgan (va hali qaytarilmagan)
    yozuvi borligini tekshiradi."""
    return Berish.objects.filter(
        kitob_id=kitob_id, nusxa__isnull=True, qaytarilgan_sana__isnull=True
    ).exists()


def kitob_ber_by_kitob(kitob, oquvchi, xodim):
    """Kitob bo'yicha berish — qaysi holatda nima qilinishini hal qiladi:

    * mavjud nusxa bor -> shu nusxa beriladi;
    * nusxa yo'q -> kitob «asli» holatda beriladi (berish/tasks xabari);
    * nusxalari bor, lekin hammasi band/berilgan -> xato chiqadi va
      o'quvchi avtomatik navbatga qo'shiladi.

    Bu funksiya o'zi `transaction.atomic` emas: «barcha nusxalar berilgan»
    xatosi chiqarilganda navbat yozuvi saqlanib qolishi kerak — atomic
    blok ichida esa butun tranzaksiya bekor qilinib, navbat ham yo'qolardi.
    Nusxa esa `kitob_ber` ichida `select_for_update` bilan qayta bloklanadi.
    """
    nusxa = Nusxa.objects.filter(kitob=kitob, holati="mavjud").order_by("id").first()
    if nusxa:
        return kitob_ber(nusxa, oquvchi, xodim)

    if Nusxa.objects.filter(kitob=kitob).exists():
        natija = navbatga_qosh(kitob, oquvchi)
        _xato(
            "barcha_nusxalar_berilgan",
            "Bu kitobning barcha nusxalari berilgan. O'quvchi navbatga qo'shildi",
            navbat_id=natija.navbat.id,
            orin=natija.orin,
            navbatga_qoshildi=natija.yangi,
        )

    return kitob_ber(None, oquvchi=oquvchi, kitob=kitob, xodim=xodim)


@transaction.atomic
def kitob_ber(nusxa, oquvchi, xodim, kitob=None):
    """Kitob berish: barcha biznes cheklovlarni tekshiradi, so'ng nusxa
    holatini va Berish yozuvini bitta tranzaksiyada o'zgartiradi.

    Ikki xil berish bor:
    * `nusxa` berilsa — aniq nusxa beriladi (nusxa holati tekshiriladi);
    * `nusxa=None` va `kitob` berilsa — nusxasi yo'q kitob «asli» holatda
      beriladi (bunda `bergan_xodim` bo'sh qoldirilishi mumkin).
    """
    _oq_berish_cheklovlari(oquvchi)

    if nusxa is None:
        if kitob is None:
            _xato("notogri_manzil", "Nusxa yoki kitobni tanlang")
        kitob = Kitob.objects.select_for_update().get(pk=kitob.pk)
        if Nusxa.objects.filter(kitob_id=kitob.pk).exists():
            _xato(
                "nusxa_mavjud",
                "Bu kitobning nusxasi bor — nusxa orqali bering",
            )
        if faol_asli_berish(kitob.pk):
            _xato("kitob_band", "Bu kitob «asli» holda berilgan")
        nusxa_holati = None
        kitob_id = kitob.pk
    else:
        nusxa = Nusxa.objects.select_for_update().get(pk=nusxa.pk)
        if nusxa.holati != "mavjud":
            _xato("nusxa_band", "Bu nusxa hozir mavjud emas")
        kitob_id = nusxa.kitob_id
        nusxa_holati = "berilgan"
        kitob = nusxa.kitob

    if nusxa_holati:
        nusxa.holati = nusxa_holati
        nusxa.save(update_fields=["holati"])

    berish = Berish.objects.create(
        nusxa=nusxa,
        kitob_id=kitob_id,
        oquvchi=oquvchi,
        bergan_xodim=xodim,
        qaytarish_muddati=now().date() + timedelta(days=settings.MUDDAT_KUN),
        holati="faol",
    )

    # Kitobning o'z holati ham nusxalardan (va «asli» berish yozuvidan)
    # kelib chiqib yangilanadi — aks holda kitob ro'yxatida «Mavjud» deb
    # ko'rinib turar edi. Yozuv yaratilgandan keyin chaqiriladi, chunki
    # «asli» berishda faqat shu yozuv borligi «Berilgan» holatini beradi.
    kitob_holatini_yenila(kitob_id)

    # Foydalanuvchi tayinlagan navbat (band) endi berilganligi tasdiqlanadi.
    # taklif_xabari_yuborilgan=False: o'quvchi allaqachon "Kitob berildi"
    # xabarini oladi, taklif xabari esa kerak emas (takroriy xabar bo'lmasin).
    Navbat.objects.filter(
        kitob_id=kitob_id,
        oquvchi=oquvchi,
        holati__in=["kutmoqda", "taklif_qilindi"],
    ).update(
        holati="yakunlandi",
        javob_vaqti=now(),
        taklif_xabari_yuborilgan=False,
    )

    # Kitob olgan kundan boshlab qaytarish muddati (14 kun) boshlanadi.
    transaction.on_commit(lambda: _kitob_berildi_xabarini_yubor(berish))

    return berish


def _kitob_berildi_xabarini_yubor(berish):
    """Berish tranzaksiyasi commit bo'lgach, o'quvchiga Telegram xabar yuboradi:
    «Kitob berildi» + qaytarish muddati + olgan kundan hisoblanadigan muddat."""
    oquvchi = berish.oquvchi
    if not oquvchi.telegram_id:
        return
    if berish.nusxa_id:
        manzil = f"Inventar raqami: {berish.nusxa.inventar_raqami}"
    else:
        manzil = "Nusxasi yo'q — kitob aslida berildi"
    matn = (
        "📖 <b>Kitob berildi!</b>\n\n"
        f"Qabul qilgan kitobingiz: <b>{telegram_escape(berish.kitob.nomi)}</b>\n"
        f"{manzil}\n"
        f"Berilgan sana: {berish.berilgan_sana}\n"
        f"Qaytarish muddati: <b>{berish.qaytarish_muddati}</b>\n\n"
        f"Sizda kitobni olgan kundan boshlab {settings.MUDDAT_KUN} kun muddat bor. "
        "Iltimos, vaqtida topshiring!"
    )
    telegram_xabar_yubor(oquvchi.telegram_id, matn)


@transaction.atomic
def kitob_qaytar(berish, xodim):
    """Kitobni qaytarib olish: avval nusxani bo'shatadi (nusxasiz «asli»
    kitobda esa faqat yozuv yopiladi), jarimani hisoblaydi (bor bo'lsa),
    so'ng navbatdagi keyingi odamga taklif yuboradi (bo'lsa)."""
    berish = Berish.objects.select_for_update().get(pk=berish.pk)
    berish.qaytarilgan_sana = now().date()
    berish.olgan_xodim = xodim
    berish.holati = "qaytarilgan"
    berish.save()

    taklif_ketdi = False
    if berish.nusxa_id:
        nusxa = Nusxa.objects.select_for_update().get(pk=berish.nusxa_id)
        nusxa.holati = "mavjud"
        nusxa.save(update_fields=["holati"])

        # Nusxa bo'shatildi — kitob holati ham qayta "Mavjud" ga qaytadi
        # (agar boshqa mavjud nusxa bo'lsa, allaqachon "Mavjud" bo'lib qoladi).
        kitob_holatini_yenila(nusxa.kitob_id)

        jarima = jarimani_hisobla(berish)
        taklif_ketdi = keyingi_navbatga_taklif_yubor(nusxa.id)
    else:
        # «Asli» kitob qaytarildi — nusxa yo'q, faqat kitob holati va
        # navbatni bo'shatamiz (keyingi navbatdagiga taklif yuborilmaydi).
        kitob_holatini_yenila(berish.kitob_id)
        jarima = jarimani_hisobla(berish)

    return berish, jarima, taklif_ketdi
