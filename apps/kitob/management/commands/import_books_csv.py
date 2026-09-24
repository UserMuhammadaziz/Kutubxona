"""
artistic-literature.csv dagi kitoblarni bazaga import qiladi.

Ishlatish: python manage.py import_books_csv
"""
import csv
import re
from decimal import Decimal, InvalidOperation
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from kitob.models import Kitob

BASE_DIR = "."

HEADERS = {
    "nomi": "Badiiy adabiyot nomi",
    "muallif": "Muallif nomi",
    "isbn": "ISBN",
    "til_yozuv": "Kitob tili",
    "turi": "Badiiy adabiyot turi",
    "nashr_yili": "Nashr yili",
    "nashriyot": "Nashriyot nomi",
    "buyurtma_soni": "Buyurtma soni",
    "narh": "Narxi",
}

JANR_MAP = {
    "badiiy adabiyot": "badiiy",
    "bolalar adabiyoti": "bolalar",
    "o'quv-metodik adabiyot": "darslik",
    "ma'lumotnoma va lug'at": "boshqa",
    "siyosiy-iqtisodiy adabiyot": "boshqa",
}

TIL_MAP = {
    "o`zbek tili": "ozbek_lotin",
    "ozbek tili": "ozbek_lotin",
    "ўзбек тили": "ozbek_krill",
    "uzbek tili": "ozbek_lotin",
    "rus tili": "rus",
    "ingliz tili": "ingliz",
}

YIL_WORDS = re.compile(r"^(19\d\d|20\d\d)$")


def _to_int(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _to_decimal(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        d = Decimal(value)
        return d
    except InvalidOperation:
        return None


def _norm_nashriyot(value):
    value = (value or "").strip()
    if not value:
        return ""
    if YIL_WORDS.match(value):
        return ""
    return value


class Command(BaseCommand):
    help = "artistic-literature.csv faylidagi kitoblarni bazaga import qiladi"

    def add_arguments(self, parser):
        parser.add_argument("--file", default="artistic-literature.csv")
        parser.add_argument("--dry-run", action="store_true", help="Hech narsa yozmasdan faqat hisoblaydi")

    @transaction.atomic
    def handle(self, *args, **options):
        path = options["file"]
        try:
            with open(path, encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except FileNotFoundError:
            raise CommandError(f"Fayl topilmadi: {path}")

        created = updated = skipped = 0
        isbn_missing = set()
        mavjud = ["mavjud"]
        page = 50
        for i, row in enumerate(rows, start=1):
            nomi = (row.get(HEADERS["nomi"]) or "").strip()
            muallif = (row.get(HEADERS["muallif"]) or "").strip()
            if not nomi:
                skipped += 1
                continue

            nashr_yili = _to_int(row.get(HEADERS["nashr_yili"]))
            yil_now = date.today().year
            if nashr_yili is None:
                nashr_yili = 2000
            elif nashr_yili < 1400 or nashr_yili > yil_now:
                nashr_yili = 2000

            isbn = (row.get(HEADERS["isbn"]) or "").strip()
            if isbn and isbn in isbn_missing:
                isbn = ""
            if isbn:
                isbn_missing.add(isbn)

            til_yozuv = (row.get(HEADERS["til_yozuv"]) or "").strip().lower()
            til = TIL_MAP.get(til_yozuv, "boshqa")

            turi = (row.get(HEADERS["turi"]) or "").strip().lower()
            turi = turi.replace("ʻ", "'").replace("ʼ", "'").replace("’", "'")
            janr = JANR_MAP.get(turi, "boshqa")

            holat = (row.get("Holati") or "").strip().lower()
            holati = "mavjud" if holat in ("mavjud", "") else holat

            buyurtma_soni = _to_int(row.get(HEADERS["buyurtma_soni"]))
            if buyurtma_soni is not None and buyurtma_soni <= 0:
                buyurtma_soni = None
            narh = _to_decimal(row.get(HEADERS["narh"]))
            if narh is not None and narh <= 0:
                narh = None
            nashriyot = _norm_nashriyot(row.get(HEADERS["nashriyot"]))

            defaults = dict(
                isbn=isbn or None,
                janr=janr,
                til=til,
                narh=narh,
                buyurtma_soni=buyurtma_soni,
                holati=holati,
                nashriyot=nashriyot,
            )
            if options["dry_run"]:
                if Kitob.objects.filter(
                    nomi=nomi, muallif=muallif, nashr_yili=nashr_yili
                ).exists():
                    updated += 1
                else:
                    created += 1
                continue

            obj, yaratildi = Kitob.objects.get_or_create(
                nomi=nomi,
                muallif=muallif,
                nashr_yili=nashr_yili,
                defaults=defaults,
            )
            if yaratildi:
                created += 1
            else:
                updated += 1

            if i % page == 0:
                self.stdout.write(f"... {i} qator ishlab chiqildi")

        self.stdout.write(self.style.SUCCESS(
            f"Tayyor: {created} ta yangi kitob qo'shildi, {updated} ta mavjud bo'lib o'tkazib yuborildi, "
            f"{skipped} ta bo'sh qator o'tkazib yuborildi. (jami {len(rows)} qator)"
        ))