from django.db import migrations


def kitob_holatlarini_sinxron_qil(apps, schema_editor):
    """`Kitob.holati` avval hech qachon yangilanmagan edi — u doim `mavjud`
    qolardi. Endi u nusxalar holatidan avtomatik hisoblanadi
    (`kitob.services.kitob_holatini_yenila`), shuning uchun mavjud
    ma'lumotni bir marta to'g'rilaymiz.

    Logika:
      * kamida bitta `mavjud` nusxa -> "mavjud"
      * `mavjud` yo'q, lekin `berilgan` nusxa bor -> "berilgan"
      * aks holda -> "mavjud"

    «Yo'qolgan» qo'lda belgilangan doimiy holat bo'lgani uchun tegilmaydi.
    """
    Kitob = apps.get_model("kitob", "Kitob")
    Nusxa = apps.get_model("nusxa", "Nusxa")

    holatlar = {}
    for nusxa_id, kitob_id, holati in Nusxa.objects.values_list("id", "kitob_id", "holati"):
        holatlar.setdefault(kitob_id, set()).add(holati)

    yangilanadilar = []
    for kitob in Kitob.objects.all().only("id", "holati"):
        if kitob.holati == "yoqolgan":
            continue

        nusxa_holatlari = holatlar.get(kitob.id, set())
        if "mavjud" in nusxa_holatlari:
            yangi = "mavjud"
        elif "berilgan" in nusxa_holatlari:
            yangi = "berilgan"
        else:
            yangi = "mavjud"

        if kitob.holati != yangi:
            kitob.holati = yangi
            yangilanadilar.append(kitob)

    if yangilanadilar:
        Kitob.objects.bulk_update(yangilanadilar, ["holati"], batch_size=500)


def kitob_holatlarini_tezlash(apps, schema_editor):
    """Data migratsiyasi — qaytarish uchun hech narsa qilmaydi."""


class Migration(migrations.Migration):
    dependencies = [
        ("kitob", "0005_alter_kitob_holati"),
    ]

    operations = [
        migrations.RunPython(
            kitob_holatlarini_sinxron_qil,
            kitob_holatlarini_tezlash,
        ),
    ]