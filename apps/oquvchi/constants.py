"""Ariza formati uchun umumiy qoidalar.

Aiogram bot (`bot/fanlar.py`) bu ro'yxatning nusxasidan foydalanadi —
bot Django kodini import qila olmaganligi uchun ikki nusxa mavjud. Fan
qo'shganda ikkala faylni ham yangilash kerak.
"""

import re

FANLAR = [
    "Matematika",
    "Ona tili",
    "O'zbek tili",
    "Adabiyot",
    "Fizika",
    "Kimyo",
    "Biologiya",
    "Tarix",
    "Geografiya",
    "Informatika",
    "Ingliz tili",
    "Rus tili",
    "Tasviriy san'at",
    "Musiqa",
    "Jismoniy tarbiya",
    "Texnologiya",
    "Ijtimoiy fanlar",
    "Tabiiy fanlar",
    "Huquq",
    "Iqtisodiyot",
    "Algebra",
    "Chizmachilik",
    "Geometriya",
    "Logoped",
]

# 1—11-sinf va ixtiyoriy litra: 7-A, 9-B, 10-, 11-V.
SINF_RE = re.compile(r"^(?:[1-9]|1[01])-[A-Za-z]?$")

# Kamida ikki so'z: «Ism Familiya». Defis/apostrof ichida qoldiriladi.
FISH_RE = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)+$", re.UNICODE)

# +998 va 9 raqam: +998901234567.
TELEFON_RE = re.compile(r"^\+998\d{9}$")


def format_xatolari(*, fish, telefon, rol, sinf, kasb):
    """Format qoidalari buzilgan maydonlar ro'yxati.

    Bo'sh ro'yxat — ariza/to'g'ri formatda. `Ariza` va `Oquvchi` yozuvlarini
    audit qilishda (migratsiya, testlar, ikkinchi bot) bitta manbadan
    foydalanish uchun.
    """
    xatolar = []
    toza_fish = (fish or "").strip()
    if len(toza_fish) > 130 or not FISH_RE.fullmatch(toza_fish):
        xatolar.append("fish")
    if not TELEFON_RE.fullmatch((telefon or "").strip()):
        xatolar.append("telefon")

    toza_sinf = (sinf or "").strip()
    toza_kasb = (kasb or "").strip()
    if (rol or "oquvchi") == "oqituvchi":
        if toza_sinf:
            xatolar.append("sinf")
        fanlar = [fan.strip() for fan in toza_kasb.split(",") if fan.strip()]
        if not fanlar or len(toza_kasb) > 60 or any(f not in FANLAR for f in fanlar):
            xatolar.append("kasb")
    else:
        if not toza_sinf or not SINF_RE.fullmatch(toza_sinf):
            xatolar.append("sinf")
        if toza_kasb:
            xatolar.append("kasb")
    return xatolar
