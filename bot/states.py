from aiogram.fsm.state import State, StatesGroup


class BogClash(StatesGroup):
    """/start — kartani bog'lash."""

    karta = State()
    telefon = State()


class Qidiruv(StatesGroup):
    """Kitob qidirish matnini kutish."""

    matn = State()


class KutubxonachiQaytarish(StatesGroup):
    """Kutubxonachi: inventar raqami orqali kitobni qaytarib olish (ixtiyoriy)."""

    inventar = State()