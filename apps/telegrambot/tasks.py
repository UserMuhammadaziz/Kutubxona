from celery import shared_task
from django.utils import timezone

from config.telegram import telegram_escape, telegram_xabar_yubor
from organization.models import Organization
from oquvchi.models import Oquvchi

from .models import KitobXabari
from .services import botni_ol


def _qisqa_avail_nomi(kitob):
    jami = kitob.nusxalar.count()
    mavjud = kitob.nusxalar.filter(holati="mavjud").count()
    if not jami:
        return "Nusxalar yo'q — «asli» holatda berilishi mumkin"
    if mavjud:
        return f"Mavjud: {mavjud} / Jami: {jami} — hozir olish mumkin"
    return f"Mavjud: 0 / Jami: {jami} — hozir barcha berilgan (navbatga yozilish mumkin)"


@shared_task
def yangi_kitob_xabari_yubor(kitob_id):
    from kitob.models import Kitob

    kitob = Kitob.objects.select_related("organization").filter(pk=kitob_id).first()
    if not kitob or not kitob.organization:
        return "skip"
    if not kitob.organization.kitob_xabarlari_yoqilgan:
        return "disabled"
    xabar, _ = KitobXabari.objects.get_or_create(
        organization=kitob.organization, kitob=kitob, tur="yangi"
    )
    if xabar.yuborildi:
        return "already"
    bot = botni_ol(kitob.organization)
    if not bot or bot.holati != "ulangan":
        return "no_bot"

    qisqa = _qisqa_avail_nomi(kitob)
    batafsil = (
        f"📚 <b>YANGI KITOB QO'SHILDI</b>\n\n"
        f"Nom: <b>{telegram_escape(kitob.nomi)}</b>\n"
        f"Muallif: {telegram_escape(kitob.muallif)}\n"
        f"Janr: {telegram_escape(kitob.get_janr_display())}\n"
        f"Nashr yili: {kitob.nashr_yili}\n"
        f"Til: {telegram_escape(kitob.get_til_display()) if kitob.til else '-'}\n"
        f"ISBN: {telegram_escape(kitob.isbn) if kitob.isbn else '-'}\n\n"
        f"<b>Holati (batafsil):</b> {telegram_escape(qisqa)}\n"
        f"<b>Qisqacha:</b> {'Mavjud' if kitob.nusxalar.filter(holati='mavjud').count() else 'Hozirda yo\\'q'}\n"
    )
    if kitob.tavsif:
        batafsil += f"\nTavsif: {telegram_escape(kitob.tavsif[:200])}"

    yuborilgan = 0
    qabul = (
        Oquvchi.objects.filter(
            organization=kitob.organization, faol=True, telegram_id__isnull=False
        )
        .values_list("telegram_id", flat=True)
        .distinct()
    )
    for tid in qabul:
        if telegram_xabar_yubor(
            tid,
            batafsil,
            organization=kitob.organization,
            bot=bot,
        ):
            yuborilgan += 1
    xabar.yuborildi = True
    xabar.yuborilgan_soni = yuborilgan
    xabar.yuborilgan_sana = timezone.now()
    xabar.save(update_fields=["yuborildi", "yuborilgan_soni", "yuborilgan_sana"])
    return f"{yuborilgan}"
