from aiogram.fsm.state import State, StatesGroup


class BogClash(StatesGroup):
    """/start — kartani bog'lash."""

    karta = State()
    telefon = State()


class Ariza(StatesGroup):
    """A'zolik arizasi: ism -> telefon -> tug'ilgan sana -> manzil."""

    fish = State()
    telefon = State()
    tugilgan_sana = State()
    manzil = State()


class Qidiruv(StatesGroup):
    """Kitob qidirish matnini kutish."""

    matn = State()


class KutubxonachiQaytarish(StatesGroup):
    """Kutubxonachi: inventar raqami orqali kitobni qaytarib olish (ixtiyoriy)."""

    inventar = State()