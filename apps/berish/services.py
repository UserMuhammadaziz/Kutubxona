from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from config.telegram import telegram_escape, telegram_xabar_yubor
from jarima.models import Jarima
from jarima.services import jarimani_hisobla
from kitob.models import Kitob
from kitob.services import faol_band_bormi, faol_bandni_top, kitob_holatini_yenila
from navbat.models import Navbat
from navbat.services import (
    keyingi_navbatga_taklif_yubor,
    navbatga_qosh,
    navbatni_mavjud_nusxa_bilan_ishga_tushir,
)
from nusxa.models import Nusxa
from oquvchi.models import Oquvchi
from .models import Berish


def _xato(kod, detail, **qoshimcha):
    raise ValidationError({"error": kod, "detail": detail, **qoshimcha})


def _oq_berish_cheklovlari(oquvchi):
    """Kitob berishdan oldin o'quvchi bo'yicha umumiy cheklovlar: faollik,
    bir vaqtda oladigan kitob limiti va to'lanmagan jarima."""
    if not oquvchi.faol:
        _xato("oquvchi_bloklangan", "O'quvchi bloklangan")

    org = oquvchi.organization
    limit = org.limit_kitob if org else settings.LIMIT_KITOB
    faol_soni = Berish.objects.filter(oquvchi=oquvchi, qaytarilgan_sana__isnull=True).count()
    if faol_soni >= limit:
        _xato("limit_oshdi", f"O'quvchida allaqachon {limit} ta kitob bor")

    jarimalar = Jarima.objects.filter(berish__oquvchi=oquvchi, tolandimi=False)
    if org is not None:
        jarimalar = jarimalar.filter(organization=org)
    if jarimalar.exists():
        _xato("tolanmagan_jarima", "O'quvchida to'lanmagan jarima bor")


def faol_asli_berish(kitob_id):
    """Nusxasi yo'q kitobning «asli» holda berilgan (va hali qaytarilmagan)
    yozuvi borligini tekshiradi."""
    return Berish.objects.filter(
        kitob_id=kitob_id, nusxa__isnull=True, qaytarilgan_sana__isnull=True
    ).exists()


def kitob_ber_by_kitob(kitob, oquvchi, xodim, band_tasdiqlandi=False):
    """Kitob bo'yicha berish — qaysi holatda nima qilinishini hal qiladi:

    * kitob band qilingan bo'lsa -> hech kimga berilmaydi (`band_tasdiqlandi`
      faqat band tasdiqlanayotganda `True` bo'ladi);
    * mavjud nusxa bor -> shu nusxa beriladi;
    * nusxa yo'q -> kitob «asli» holatda beriladi (berish/tasks xabari);
    * nusxalari bor, lekin hammasi band/berilgan -> xato chiqadi va
      o'quvchi avtomatik navbatga qo'shiladi.

    Bu funksiya o'zi `transaction.atomic` emas: «barcha nusxalar berilgan»
    xatosi chiqarilganda navbat yozuvi saqlanib qolishi kerak — atomic
    blok ichida esa butun tranzaksiya bekor qilinib, navbat ham yo'qolardi.
    Nusxa esa `kitob_ber` ichida `select_for_update` bilan qayta bloklanadi.
    """
    if not band_tasdiqlandi and faol_band_bormi(kitob.pk):
        band = faol_bandni_top(kitob.pk)
        _xato(
            "kitob_band_qilingan",
            "Bu kitob band qilingan — uni faqat kutubxonachi tasdiqlagandan "
            "keyin berish mumkin",
            band_id=band.pk if band else None,
            oquvchi=band.oquvchi.fish if band else None,
        )

    nusxa = Nusxa.objects.filter(kitob=kitob, holati="mavjud").order_by("id").first()
    if nusxa:
        return kitob_ber(nusxa, oquvchi, xodim, band_tasdiqlandi=band_tasdiqlandi)

    if Nusxa.objects.filter(kitob=kitob).exists():
        natija = navbatga_qosh(kitob, oquvchi)
        _xato(
            "barcha_nusxalar_berilgan",
            "Bu kitobning barcha nusxalari berilgan. O'quvchi navbatga qo'shildi",
            navbat_id=natija.navbat.id,
            orin=natija.orin,
            navbatga_qoshildi=natija.yangi,
        )

    return kitob_ber(
        None, oquvchi=oquvchi, kitob=kitob, xodim=xodim,
        band_tasdiqlandi=band_tasdiqlandi,
    )


@transaction.atomic
def kitob_ber(nusxa, oquvchi, xodim, kitob=None, band_tasdiqlandi=False):
    """Kitob berish: barcha biznes cheklovlarni tekshiradi, so'ng nusxa
    holatini va Berish yozuvini bitta tranzaksiyada o'zgartiradi.

    Ikki xil berish bor:
    * `nusxa` berilsa — aniq nusxa beriladi (nusxa holati tekshiriladi);
    * `nusxa=None` va `kitob` berilsa — nusxasi yo'q kitob «asli» holatda
      beriladi (bunda `bergan_xodim` bo'sh qoldirilishi mumkin).

    `band_tasdiqlandi=True` faqat `kitob.services.band_qilishni_tasdiqla`
    ichidan chaqiriladi: band qilingan kitobni aynan tasdiqlash yo'li orqali
    berish kerak, aks holda bandning o'zi berishni bloklab qo'yardi.
    """
    # O'quvchi qatorini bloklash shart: limit tekshiruvi `count()` bilan
    # bajariladi va ikki parallel so'rov (kutubxonachi ikki nusxa bir vaqtda
    # berishi) limitni oshib ketishga olib kelardi — 3 limiti bilan 4 ta
    # faol berish yaratilishi mumkin edi. `select_for_update` shu qatorni
    # bloklab, tekshiruv va yozuvni ketma-ketlashtiradi.
    oquvchi = Oquvchi.objects.select_for_update().get(pk=oquvchi.pk)
    _oq_berish_cheklovlari(oquvchi)
    organization = oquvchi.organization

    if nusxa is None:
        if kitob is None:
            _xato("notogri_manzil", "Nusxa yoki kitobni tanlang")
        kitob = Kitob.objects.select_for_update().get(pk=kitob.pk)
        if organization is not None and kitob.organization_id != organization.pk:
            _xato("boshqa_kutubxona", "Kitob boshqa kutubxonaga tegishli")
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
        if organization is not None and kitob.organization_id != organization.pk:
            _xato("boshqa_kutubxona", "Nusxa boshqa kutubxonaga tegishli")

    # Band himoyasi: tasdiqlanmagan band so'rovi bo'lsa kitobni hech kimga
    # berib bo'lmaydi (so'rov qiluvchiga ham — avval tasdiqlanishi kerak).
    if not band_tasdiqlandi and faol_band_bormi(kitob_id):
        band = faol_bandni_top(kitob_id)
        _xato(
            "kitob_band_qilingan",
            "Bu kitob band qilingan — uni faqat kutubxonachi tasdiqlagandan "
            "keyin berish mumkin",
            band_id=band.pk if band else None,
            oquvchi=band.oquvchi.fish if band else None,
        )

    if nusxa_holati:
        nusxa.holati = nusxa_holati
        nusxa.save(update_fields=["holati"])

    muddat = organization.muddat_kun if organization else settings.MUDDAT_KUN
    berish = Berish.objects.create(
        organization=organization,
        nusxa=nusxa,
        kitob_id=kitob_id,
        oquvchi=oquvchi,
        bergan_xodim=xodim,
        qaytarish_muddati=now().date() + timedelta(days=muddat),
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

    # Kitob olgan kundan boshlab qaytarish muddati boshlanadi.
    try:
        from telegrambot.models import KitobXabari

        KitobXabari.objects.get_or_create(
            organization=berish.organization, kitob=kitob, tur="berildi"
        )
        from telegrambot.tasks import yangi_kitob_xabari_yubor

        yangi_kitob_xabari_yubor.delay(kitob_id=kitob.pk)
    except Exception:
        pass
    transaction.on_commit(lambda: _kitob_berildi_xabarini_yubor(berish))

    return berish


def _kitob_berildi_xabarini_yubor(berish):
    """Berish tranzaksiyasi commit bo'lgach, o'quvchiga Telegram xabar yuboradi."""
    oquvchi = berish.oquvchi
    if not oquvchi.telegram_id:
        return
    if berish.nusxa_id:
        manzil = "Inventar raqami: " + str(berish.nusxa.inventar_raqami)
    else:
        manzil = "Nusxasi yo'q - kitob aslida berildi"
    from django.conf import settings
    if berish.organization:
        muddat = berish.organization.muddat_kun
    else:
        muddat = settings.MUDDAT_KUN
    kim = oquvchi.fish
    if getattr(oquvchi, "rol", None) == "oqituvchi":
        kim_rol = "O'qituvchi"
        kim_sinf_kasb = getattr(oquvchi, "kasb", None) or "-"
    else:
        kim_rol = "O'quvchi"
        kim_sinf_kasb = getattr(oquvchi, "sinf", None) or "-"
    kim_qisqa = str(kim) + " (" + str(kim_sinf_kasb) + ")"
    matn = (
        "\U0001F4D6 <b>Kitob berildi!</b>\n\n"
        + "Qabul qilgan kitob: <b>" + telegram_escape(berish.kitob.nomi) + "</b>\n"
        + "Muallif: " + telegram_escape(berish.kitob.muallif) + "\n"
        + manzil + "\n\n"
        + "<b>Batafsil (kimga berildi):</b>\n"
        + "\u2022 Ism: " + telegram_escape(kim) + "\n"
        + "\u2022 Rol: " + telegram_escape(kim_rol) + "\n"
        + "\u2022 Sinf/Fan: " + telegram_escape(kim_sinf_kasb) + "\n"
        + "\u2022 Telefon: " + telegram_escape(oquvchi.telefon) + "\n"
        + "\u2022 Karta: " + telegram_escape(oquvchi.karta_raqami) + "\n\n"
        + "<b>Qisqacha:</b> " + telegram_escape(kim_qisqa) + " \u2014 " + telegram_escape(berish.kitob.nomi) + " berildi.\n\n"
        + "Berilgan sana: " + str(berish.berilgan_sana) + "\n"
        + "Qaytarish muddati: <b>" + str(berish.qaytarish_muddati) + "</b>\n\n"
        + "Sizda kitobni olgan kundan boshlab " + str(muddat) + " kun muddat bor. Iltimos, vaqtida topshiring!"
    )
    try:
        from oquvchi.models import Oquvchi
        from telegrambot.services import botni_ol
        from config.telegram import telegram_xabar_yubor as txy
        bot = botni_ol(berish.organization)
        if bot and bot.holati == "ulangan":
            qisqa = (
                "\U0001F4E3 <b>Kitob berildi (axborot)</b>\n\n"
                + "Kitob: <b>" + telegram_escape(berish.kitob.nomi) + "</b>\n"
                + "Muallif: " + telegram_escape(berish.kitob.muallif) + "\n"
                + "<b>Qisqacha:</b> " + telegram_escape(kim_qisqa) + " ga berildi.\n"
                + "<b>Batafsil:</b> " + telegram_escape(kim) + " | " + telegram_escape(kim_rol) + " | " + telegram_escape(kim_sinf_kasb) + " | Qaytarish: " + str(berish.qaytarish_muddati) + "\n"
                + "<b>Holat:</b> Hozir berilgan \u2014 mavjudlik soni pasaygan."
            )
            for tid in Oquvchi.objects.filter(
                organization=berish.organization, faol=True, telegram_id__isnull=False
            ).exclude(pk=oquvchi.pk).values_list("telegram_id", flat=True).distinct():
                txy(tid, qisqa, organization=berish.organization, bot=bot)
    except Exception:
        pass
    telegram_xabar_yubor(oquvchi.telegram_id, matn, organization=berish.organization)


def _erken_qaytarish_xabarini_yubor(berish):
    """Muddatdan oldin qaytarilgan kitob bo'yicha o'quvchiga Telegram xabar.

    Jarima yozilmagan, `holati='qaytarilgan'` yozuvi commit bo'lgan holatda
    chaqiriladi. Xabar yuborilmasa ham qaytarish amalga oshgan bo'ladi."""
    oquvchi = berish.oquvchi
    if not oquvchi.telegram_id:
        return
    qolgan = (berish.qaytarish_muddati - berish.qaytarilgan_sana).days
    matn = (
        "📗 <b>Kitob muddatdan oldin qaytarib olindi</b>\n\n"
        f"Kitobingiz: <b>{telegram_escape(berish.kitob.nomi)}</b>\n"
        f"Berilgan sana: {berish.berilgan_sana}\n"
        f"Qaytarish muddati: {berish.qaytarish_muddati}\n"
        f"Qaytarilgan sana: {berish.qaytarilgan_sana}\n\n"
        f"Muddatga {qolgan} kun qolgan edi. Kitobni vaqtida topshirdingiz uchun "
        "raxmat! Jarima yozilmadi.\n"
        "📚 Yana kitob olish uchun «🔎 Kitob qidirish» bo'limidan foydalanishingiz mumkin."
    )
    telegram_xabar_yubor(oquvchi.telegram_id, matn, organization=berish.organization)


@transaction.atomic
def kitob_qaytar(berish, xodim):
    """Kitobni qaytarib olish: avval nusxani bo'shatadi (nusxasiz «asli»
    kitobda esa faqat yozuv yopiladi), jarimani hisoblaydi (bor bo'lsa),
    so'ng navbatdagi keyingi odamga taklif yuboradi (bo'lsa).

    Ikkinchi marta qaytarish xatoga aylantiriladi: aks holda qaytarish sanasi
    yangilanib, jarima qayta hisoblanar va navbatdagi keyingi odamga yana
    taklif yuborilardi (bitta tugma ikki marta bosilishi yetarli)."""
    berish = Berish.objects.select_for_update().get(pk=berish.pk)
    if berish.qaytarilgan_sana:
        _xato(
            "allaqachon_qaytarilgan",
            "Bu kitob allaqachon qaytarib olingan",
            qaytarilgan_sana=str(berish.qaytarilgan_sana),
        )
    berish.qaytarilgan_sana = now().date()
    berish.olgan_xodim = xodim
    berish.holati = "qaytarilgan"
    berish.save()

    # Muddatdan oldin qaytarilganini shu yerda aniqlaymiz (keyinroq emas):
    # qaytarish muddati o'zgarmaydi, lekin o'quvchiga xabar yuborish kerakligi
    # faqat muddatdan kelib chiqadi. Jarima yozilgan holatlar "muddatdan
    # oldin" hisoblanmaydi, chunki ular kechikkan qaytarishlar.
    erken_qaytarish = berish.qaytarish_muddati > berish.qaytarilgan_sana

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
        # «Asli» kitob qaytarildi — nusxa yo'q, faqat kitob holati
        # yangilanadi. Navbatdagilar uchun «asli» holda taklif yuboriladi,
        # aks holda ular navbatda abadi kutib qolardi.
        kitob_holatini_yenila(berish.kitob_id)
        jarima = jarimani_hisobla(berish)
        taklif_ketdi = navbatni_mavjud_nusxa_bilan_ishga_tushir(berish.kitob_id)

    # Muddatdan oldin qaytarilgan bo'lsa, o'quvchiga xabar yuboriladi.
    # Xabar tranzaksiya commit bo'lgandan keyin yuboriladi (Telegram so'rovi
    # tranzaksiyani ushlab turmasligi kerak) va bu yerda emas, servisda —
    # shunda kitobni web paneldan ham, Telegram botidan ham qaytarilganda
    # xabar bir xil ishlaydi.
    if erken_qaytarish:
        transaction.on_commit(lambda: _erken_qaytarish_xabarini_yubor(berish))

    return berish, jarima, taklif_ketdi
