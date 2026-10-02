import sys
from pathlib import Path

sys.path.insert(0, str(Path("bot").resolve()))

from handlers import kutubxonachi, qidiruv, shaxsiy, start
from states import Ariza

rows = []
for mod in (start, qidiruv, shaxsiy, kutubxonachi):
    for h in mod.router.message.handlers:
        state = None
        extra = ""
        for f in h.filters:
            if f.__class__.__name__ == "StateFilter":
                state = list(f.state)[0].state
            else:
                extra = f.__class__.__name__
        name = h.callback.__name__
        rows.append((mod.router.name, name, state, extra))

print(f"Jami message handler: {len(rows)}\n")
for i, (rname, name, state, extra) in enumerate(rows):
    mark = "  <== ARIZA TELEFON" if state == Ariza.telefon else ""
    print(f"  [{i:2}] {rname:12} {name:24} {str(state or ''):18} "
          f"{extra:14}{mark}")

contact = next(i for i, r in enumerate(rows) if r[1] == "ariza_telefon")
matn = next(i for i, r in enumerate(rows) if r[1] == "ariza_telefon_matn")

print(f"\n  CONTACT handler: [{contact}] ariza_telefon")
print(f"  MATN handler:    [{matn}] ariza_telefon_matn")
assert rows[contact][2] == Ariza.telefon, "CONTACT state notog'ri"
assert rows[matn][2] == Ariza.telefon, "MATN state notog'ri"
assert contact < matn, "XATO: MATN handler CONTACT dan oldin turibdi!"
print("  TARTIB TO'G'RI: contact matn handler ga tushmaydi")
print("\nTEKSHIROV O'TDI")