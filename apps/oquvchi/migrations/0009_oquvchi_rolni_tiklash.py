# 0009: tasdiqlangan arizalardan o'quvchi rol/kasbini to'ldirish.
#
# `Oquvchi.rol` va `Oquvchi.kasb` maydonlari 0008 da qo'shildi, lekin
# undan oldin ro'yxatga olingan o'qituvchilarda bu ma'lumot yo'q edi
# (rol faqat `Ariza` da saqlanardi). Shu sababli "O'qituvchilar" bo'limi
# bo'sh ko'rinmasligi uchun ma'lumotni qayta tiklaymiz.

from django.db import migrations


def rolni_tiklash(apps, schema_editor):
    Oquvchi = apps.get_model("oquvchi", "Oquvchi")
    Ariza = apps.get_model("oquvchi", "Ariza")

    for oquvchi in Oquvchi.objects.all():
        arizalar = Ariza.objects.filter(holati="tasdiqlandi")
        ariza = arizalar.filter(telegram_id=oquvchi.telegram_id).first()
        if ariza is None and oquvchi.telefon:
            ariza = arizalar.filter(telefon=oquvchi.telefon).first()
        if ariza is None:
            continue
        if ariza.rol == "oqituvchi":
            oquvchi.rol = "oqituvchi"
            oquvchi.kasb = ariza.kasb or oquvchi.kasb
            oquvchi.sinf = oquvchi.sinf or ""
            oquvchi.save(update_fields=["rol", "kasb", "sinf"])


def teskari_holat(apps, schema_editor):
    """Ma'lumotni qaytarish shart emas: maydonlar o'z qoladi."""


class Migration(migrations.Migration):

    dependencies = [
        ("oquvchi", "0008_oquvchi_kasb_oquvchi_rol"),
    ]

    operations = [
        migrations.RunPython(rolni_tiklash, teskari_holat),
    ]