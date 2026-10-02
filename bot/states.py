from aiogram.fsm.state import State, StatesGroup


class BogClash(StatesGroup):
    """/start — kartani bog'lash."""

    karta = State()
    telefon = State()


class Ariza(StatesGroup):
    """A'zolik arizasi.

    Rol `/start` dagi inline tugmalardan tanlanadi va FSM ma'lumotlarida
    saqlanadi:
    • `rol="oquvchi"`    → ism-familiya -> telefon -> sinf;
    • `rol="oqituvchi"` → ism-familiya -> telefon -> kasb (o'qitayotgan fan).
    """

    fish = State()
    telefon = State()
    sinf = State()
    kasb = State()


class Qidiruv(StatesGroup):
    """Kitob qidirish matnini kutish."""

    matn = State()


class KutubxonachiQaytarish(StatesGroup):
    """Kutubxonachi: inventar raqami orqali kitobni qaytarib olish (ixtiyoriy)."""

    inventar = State()