p='services.py'
s=open(p,encoding='utf-8').read()
start=s.find('def _kitob_berildi_xabarini_yubor')
if start==-1: raise SystemExit('no')
end=s.find('\n\n@transaction.atomic\n', start)
if end==-1: end=s.find('\n\ndef ', start+1)
block=s[start:end]
new='''def _kitob_berildi_xabarini_yubor(berish):
    """Berish tranzaksiyasi commit bo'lgach, o'quvchiga Telegram xabar yuboradi."""
    oquvchi = berish.oquvchi
    if not oquvchi.telegram_id:
        return
    if berish.nusxa_id:
        manzil = f"Inventar raqami: {berish.nusxa.inventar_raqami}"
    else:
        manzil = "Nusxasi yo'q - kitob aslida berildi"
    muddat = berish.organization.muddat_kun if berish.organization else None
    if muddat is None:
        from django.conf import settings
        muddat = settings.MUDDAT_KUN
    kim = oquvchi.fish
    kim_rol = "O'qituvchi" if oquvchi.rol == "oqituvchi" else "O'quvchi"
    kim_sinf_kasb = oquvchi.kasb if oquvchi.rol == "oqituvchi" else (oquvchi.sinf or "-")
    kim_qisqa = f"{kim} ({kim_sinf_kasb})"
    matn = (
        "📖 <b>Kitob berildi!</b>\\n\\n"
        f"Qabul qilgan kitob: <b>{telegram_escape(berish.kitob.nomi)}</b>\\n"
        f"Muallif: {telegram_escape(berish.kitob.muallif)}\\n"
        f"{manzil}\\n\\n"
        "<b>Batafsil (kimga berildi):</b>\\n"
        f"• Ism: {telegram_escape(kim)}\\n"
        f"• Rol: {telegram_escape(kim_rol)}\\n"
        f"• Sinf/Fan: {telegram_escape(kim_sinf_kasb)}\\n"
        f"• Telefon: {telegram_escape(oquvchi.telefon)}\\n"
        f"• Karta: {telegram_escape(oquvchi.karta_raqami)}\\n\\n"
        f"<b>Qisqacha:</b> {telegram_escape(kim_qisqa)} — {telegram_escape(berish.kitob.nomi)} berildi.\\n\\n"
        f"Berilgan sana: {berish.berilgan_sana}\\n"
        f"Qaytarish muddati: <b>{berish.qaytarish_muddati}</b>\\n\\n"
        f"Sizda kitobni olgan kundan boshlab {muddat} kun muddat bor. Iltimos, vaqtida topshiring!"
    )
    try:
        from oquvchi.models import Oquvchi as OquvchiModel
        from telegrambot.services import botni_ol
        from config.telegram import telegram_xabar_yubor as txy
        bot = botni_ol(berish.organization)
        if bot and bot.holati == "ulangan":
            qisqa = (
                "📣 <b>Kitob berildi (axborot)</b>\\n\\n"
                f"Kitob: <b>{telegram_escape(berish.kitob.nomi)}</b>\\n"
                f"Muallif: {telegram_escape(berish.kitob.muallif)}\\n"
                f"<b>Qisqacha:</b> {telegram_escape(kim)} ({telegram_escape(kim_sinf_kasb)}) ga berildi.\\n"
                f"<b>Batafsil:</b> {telegram_escape(kim)} | {telegram_escape(kim_rol)} | {telegram_escape(kim_sinf_kasb)} | Qaytarish: {berish.qaytarish_muddati}\\n"
                "<b>Holat:</b> Hozir berilgan — mavjudlik soni pasaygan."
            )
            for tid in (OquvchiModel.objects.filter(organization=berish.organization, faol=True, telegram_id__isnull=False).exclude(pk=oquvchi.pk).values_list('telegram_id', flat=True).distinct()):
                txy(tid, qisqa, organization=berish.organization, bot=bot)
    except Exception:
        pass
    telegram_xabar_yubor(oquvchi.telegram_id, matn, organization=berish.organization)
'''
open(p,'w',encoding='utf-8').write(s.replace(block,new))
print('ok')
