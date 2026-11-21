"""O'zgarish kiritilgacha yuborilgan barcha ariza va qabul qilingan
o'quvchi/o'qituvchilarni «yangi formatda qaytadan ariza yuborish» ro'yxatiga
qo'shadi.

Foydalanuvchi so'rovi: ilgari belgilanmagan formatda to'ldirilgan arizalar
boshidan qayta yuborilishi kerak, kutubxonaga qabul qilinganlar ham shu
talabga kiritiladi. Shu sababli migratsiya vaqtida mavjud bo'lgan BARCHA
yozuvlar belgilanadi; yangi yozuvlar esa model default'i bo'yicha False
bo'lib qoladi.
"""

from django.db import migrations


def belgilash(apps, schema_editor):
    Ariza = apps.get_model("oquvchi", "Ariza")
    Oquvchi = apps.get_model("oquvchi", "Oquvchi")
    Ariza.objects.update(qayta_ariza_kerak=True)
    Oquvchi.objects.update(qayta_ariza_kerak=True)


class Migration(migrations.Migration):
    dependencies = [
        ("oquvchi", "0011_ariza_qayta_ariza_kerak_oquvchi_qayta_ariza_kerak"),
    ]

    operations = [migrations.RunPython(belgilash, migrations.RunPython.noop)]
