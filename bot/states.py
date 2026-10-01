from aiogram.fsm.state import State, StatesGroup


class BogClash(StatesGroup):
    """/start — kartani bog'lash."""

    karta = State()
    telefon = State()


class Ariza(StatesGroup):
    """A'zolik arizasi: ism-familiya -> telefon -> sinf.

    Atigi uch maydon so'raladi (backend ham shuncha talab qiladi)."""

    fish = State()
    telefon = State()
    sinf = State()


class Qidiruv(StatesGroup):
    """Kitob qidirish matnini kutish."""

    matn = State()


class KutubxonachiQaytarish(StatesGroup):
    """Kutubxonachi: inventar raqami orqali kitobni qaytarib olish (ixtiyoriy)."""

    inventar = State()