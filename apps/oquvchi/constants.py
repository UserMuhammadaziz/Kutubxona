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
]

# 1—11-sinf va ixtiyoriy litra: 7-A, 9-B, 10-, 11-V.
SINF_RE = re.compile(r"^(?:[1-9]|1[01])-[A-Za-z]?$")

# Kamida ikki so'z: «Ism Familiya». Defis/apostrof ichida qoldiriladi.
FISH_RE = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)+$", re.UNICODE)
