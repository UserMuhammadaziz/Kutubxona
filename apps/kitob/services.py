"""Kitob holatini nusxalar asosida avtomatik yangilash.

Kitob berilganda faqat `Nusxa.holati` o'zgaradi, lekin `Kitob.holati`
butunlay o'zgarishsiz qolardi — shuning uchun kitob ro'yxatida
«Mavjud» deb ko'rinib turar edi, garchi aslida nusxalari yo'q edi.

Bu modul kitob holatini nusxalar holatidan kelib chiqib hisoblaydi:

  * kamida bitta `mavjud` nusxa bor  -> «Mavjud»
  * `mavjud` nusxa yo'q, lekin `berilgan` nusxa bor -> «Berilgan»
  * aks holda -> «Mavjud» (nusxa yo'q yoki hammasi ta'mirda)

Muhim: «Yo'qolgan» — bu qo'lda belgilanadigan doimiy holat, shuning uchun
avtomatik yangilash uni hech qachon tegmaydi.
"""
from kitob.models import Kitob
from nusxa.models import Nusxa


def kitob_holatini_yenila(kitob_id):
    """`Kitob.holatini` nusxalar holatiga qarab yangilaydi va yangilangan
    qiymatni qaytaradi (o'zgarmagan bo'lsa ham `None` emas, joriy qiymat)."""
    nusxalar = Nusxa.objects.filter(kitob_id=kitob_id)

    mavjud_bormi = nusxalar.filter(holati="mavjud").exists()
    berilgan_bormi = nusxalar.filter(holati="berilgan").exists()

    if mavjud_bormi:
        yangi = "mavjud"
    elif berilgan_bormi:
        yangi = "berilgan"
    else:
        yangi = "mavjud"

    kitob = Kitob.objects.get(pk=kitob_id)
    if kitob.holati == "yoqolgan" or kitob.holati == yangi:
        # «Yo'qolgan» qo'lda belgilangan holat — uni saqlaymiz.
        return kitob.holati

    kitob.holati = yangi
    kitob.save(update_fields=["holati"])
    return yangi