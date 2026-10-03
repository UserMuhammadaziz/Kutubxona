"""Bot handler'larining statik tekshiruvi (`python _check.py`).

1. Ariza telefon bosqichida CONTACT va matn handler'lari to'g'ri
   ketma-ketligini tekshiradi.
2. Rol tanlash oqimidagi nomlarni tekshiradi — `ROL_UCHUNCHI_MAYDON`
   kabi nomxato serverda `NameError` berib butun oqimni buzgan edi,
   shuning uchun xabar matni shu yerda render qilib tekshiriladi.
3. Ariza yuborish xatosida state tozalanmasligi va oxirgi
   "noma_lum" router'i mavjudligini tekshiradi (bot jim qolmasligi).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path("bot").resolve()))

from handlers import kutubxonachi, noma_lum, qidiruv, shaxsiy, start
from keyboards import (
    ARIZA_ROL_OQITUVCHI,
    ARIZA_ROL_OQUVCHI,
    ARIZA_ROL_TUGMA_MATNLARI,
)
from states import Ariza

# --- 1. Rol tanlash oqimi -------------------------------------------------
print("ROL TANLASH OQIMI")
for rol in (ARIZA_ROL_OQUVCHI, ARIZA_ROL_OQITUVCHI):
    xabar = start.rol_tanlash_xabari(rol)
    assert start.ROL_TASDIQLANDI_XABARI[rol] in xabar, "rol xabari chiqmedi"
    assert start.ROL_UCHUNCHI_MAYDON[rol] in xabar, "uchinchi maydon nomi chiqmedi"
    tugma = ARIZA_ROL_TUGMA_MATNLARI[rol]
    print(f"  {rol:9} -> {tugma} | {start.ROL_UCHUNCHI_MAYDON[rol]}")
print("  TARTIB TO'G'RI: har ikki rol uchun xabar render bo'ldi\n")

# --- 2. Telefon bosqichi handlerlari --------------------------------------
# `aiogram` yangi versiyalarida state filtri `FilterObject` ichida
# `StateFilter` bo'lib keladi — ikkala shaklni ham qo'llab-quvvatlaymiz.
def _holatni_top(filter_obj):
    """Filtrdagi FSM state'ni qaytaradi (yo'q bo'lsa None).

    aiogradagi holat filtri `State` yoki eski `StateFilter` ko'rinishida
    bo'lishi mumkin — ikkalasini ham qo'llaymiz.
    """
    ichki = getattr(filter_obj, "callback", filter_obj)
    if type(ichki).__name__ == "State":
        return ichki.state
    if type(ichki).__name__ == "StateFilter":
        return list(ichki.state)[0].state
    return None


rows = []
for mod in (start, qidiruv, shaxsiy, kutubxonachi):
    for h in mod.router.message.handlers:
        state = None
        extra = ""
        for f in h.filters:
            holat = _holatni_top(f)
            if holat is not None:
                state = holat
            else:
                extra = type(getattr(f, "callback", f)).__name__
        rows.append((mod.router.name, h.callback.__name__, state, extra))

print(f"\nJami message handler: {len(rows)}\n")
for i, (rname, name, state, extra) in enumerate(rows):
    mark = "  <== ARIZA TELEFON" if state == Ariza.telefon.state else ""
    print(f"  [{i:2}] {rname:12} {name:24} {str(state or ''):18} "
          f"{extra:14}{mark}")

contact = next(i for i, r in enumerate(rows) if r[1] == "ariza_telefon")
matn = next(i for i, r in enumerate(rows) if r[1] == "ariza_telefon_matn")

print(f"\n  CONTACT handler: [{contact}] ariza_telefon")
print(f"  MATN handler:    [{matn}] ariza_telefon_matn")
assert rows[contact][2] == Ariza.telefon.state, "CONTACT state notog'ri"
assert rows[matn][2] == Ariza.telefon.state, "MATN state notog'ri"
assert contact < matn, "XATO: MATN handler CONTACT dan oldin turibdi!"
print("  TARTIB TO'G'RI: contact matn handler ga tushmaydi")

# --- 3. Bot jim qolmasligi -------------------------------------------------
print("\nJIM QOLMASLIK TEKSHIROVI")

# 3a. /bekor buyrug'i ro'yxatda bor (ariza to'ldirishdan voz kechish)
bekor = [h for h in start.router.message.handlers if h.callback.__name__ == "ariza_bekor_qilish"]
assert bekor, "/bekor handler'i topilmadi"
print("  /bekor handler'i: bor")

# 3b. Ariza yuborishda validatsiya xatosi state'ni tozalamasligi kerak —
# aks holda foydalanuvchi qayta yozsa bot jim qoladi.
manba = (Path("bot") / "handlers" / "start.py").read_text(encoding="utf-8")
qism = manba.split("async def _arizani_yuborish")[1]
# `state.clear()` faqat terminal kodlar (allaqachon_azo / ariza_kutmoqda)
# tekshirilgandan KEYIN kelishi kerak.
oldindagi = qism.split("except ApiXato as e:")[1].split("await state.clear()")[0]
assert 'e.kod in ("allaqachon_azo", "ariza_kutmoqda")' in oldindagi, (
    "XATO: terminal xatolar ajratilmagan — validatsiya xatosida ham state "
    "tozalanib, foydalanuvchi qayta yozsa bot javob bermaydi"
)
# Validatsiya xatosida savol qayta takrorlanadi (savol parametridan).
assert "{savol}" in qism, "XATO: xatodan keyin savol takrorlanmayapti"
print("  xatodan keyin state saqlanadi, savol qayta takrorlanadi: to'g'ri")

# 3c. Hech qanday handler ishga tushmagan xabarlar uchun oxirgi router
assert noma_lum.router.message.handlers, "noma_lum router'i bo'sh"
assert not noma_lum.router.message.handlers[0].filters, (
    "XATO: noma_lum handler'i filtrsiz bo'lishi kerak (barcha xabarlar uchun)"
)
print("  noma_lum router'i (jim qolmaslik): filtrsiz, mavjud")

print("\nTEKSHIROV O'TDI")