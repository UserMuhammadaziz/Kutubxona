"""Ariza va kitobxonlarni format bo'yicha qayta audit qilish.

0012 migratsiya vaqtidagi BARCHA yozuvlarni «qaytadan ariza yuborishga»
belgilagan edi. Bu migratsiya format qoidalari asosida holatni qayta ko'rib
chiqadi:

* noto'g'ri formatdagi ariza/kitobxon — ``qayta_ariza_kerak=True``
  (ya'ni Arizalar, Qabul qilingan arizalar va O'quvchi/o'qituvchilar
  bo'limidagi barcha buzilgan yozuvlar majburiy ravishda qayta yuboriladi);
* to'g'ri formatdagilar — ``False`` (keraksiz qayta yuborish talab qilinmaydi).

Qoidalar `apps/oquvchi/constants.py` dagi qoidalarning nusxasi (migratsiya
kelajakda o'zgarmasligi uchun qiymatlar shu yerga kiritildi).
"""
import re

from django.db import migrations

FISH_RE = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)+$", re.UNICODE)
SINF_RE = re.compile(r"^(?:[1-9]|1[01])-[A-Za-z]?$")
TELEFON_RE = re.compile(r"^\+998\d{9}$")
FANLAR = {
    "Matematika", "Ona tili", "O'zbek tili", "Adabiyot", "Fizika", "Kimyo",
    "Biologiya", "Tarix", "Geografiya", "Informatika", "Ingliz tili",
    "Rus tili", "Tasviriy san'at", "Musiqa", "Jismoniy tarbiya",
    "Texnologiya", "Ijtimoiy fanlar", "Tabiiy fanlar", "Huquq",
    "Iqtisodiyot", "Algebra", "Chizmachilik", "Geometriya", "Logoped",
}


def notogri_formatmi(obj):
    sabab = False
    fish = (obj.fish or "").strip()
    if len(fish) > 130 or not FISH_RE.fullmatch(fish):
        sabab = True
    if not TELEFON_RE.fullmatch((obj.telefon or "").strip()):
        sabab = True

    sinf = (obj.sinf or "").strip()
    kasb = (obj.kasb or "").strip()
    rol = getattr(obj, "rol", "oquvchi") or "oquvchi"
    if rol == "oqituvchi":
        if sinf:
            sabab = True
        fanlar = [fan.strip() for fan in kasb.split(",") if fan.strip()]
        if not fanlar or len(kasb) > 60 or any(f not in FANLAR for f in fanlar):
            sabab = True
    else:
        if not sinf or not SINF_RE.fullmatch(sinf):
            sabab = True
        if kasb:
            sabab = True
    return sabab


def qayta_belgilash(apps, schema_editor):
    for model_nomi in ("Ariza", "Oquvchi"):
        model = apps.get_model("oquvchi", model_nomi)
        # `rol` ustuni 0007/0008 migratsiyalarida default qiymat bilan
        # qo'shilgan, shuning uchun hamma yozuvda mavjud.
        for obj in model.objects.all().only(
            "id", "fish", "telefon", "rol", "sinf", "kasb", "qayta_ariza_kerak"
        ).iterator():
            kerak = notogri_formatmi(obj)
            if obj.qayta_ariza_kerak != kerak:
                model.objects.filter(pk=obj.pk).update(qayta_ariza_kerak=kerak)


class Migration(migrations.Migration):
    dependencies = [
        ("oquvchi", "0012_eski_arizalar_qayta_yuborilsin"),
    ]

    operations = [migrations.RunPython(qayta_belgilash, migrations.RunPython.noop)]
