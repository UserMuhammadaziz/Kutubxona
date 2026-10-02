"""
O'quvchiga bog'lanmagan (yoki o'chirilgan) jarimalarni tozalash.

Muammo: agar `Oquvchi` yozuvi bazadan o'chirilsa, uning `Ariza` va
`Jarima` qatorlari qolib ketishi mumkin. Natijada o'sha o'quvchining
jarimalari hech qaerda ko'rinmaydi, lekin "to'lanmagan qarz" sifatida
hisobda turibdi va eslatma vazifasi ularni doimiy qayta ko'rib chiqadi.

Bu command:
  * o'quvchi yo'q jarimalarni (berish/o'quvchi FK buzilgan yoki
    o'quvchi `faol=False` bo'lgan holatlar) ro'yxat qiladi,
  * `--o'chirish` berilsa faqat shularni o'chiradi.

Ishlatish:
    python manage.py tozalash_jarimalar# faqat ko'rsatadi (o'chirmaydi)
    python manage.py tozalash_jarimalar --o'chirish    # haqiqatan o'chiradi

Xavfsizlik: hech qanday o'chirish `--o'chirish` flagisiz bajarilmaydi.
Bu moliyaviy ma'lumot, shuning uchun avval `--o'chirish`siz ko'rib chiqing.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from berish.models import Berish
from jarima.models import Jarima
from oquvchi.models import Ariza, Oquvchi


class Command(BaseCommand):
    help = (
        "O'quvchiga bog'lanmagan yoki nofaol o'quvchilarning to'lanmagan "
        "jarimalarini ko'rsatadi va `--o'chirish` bilan o'chiradi."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--o'chirish",
            action="store_true",
            help="Ko'rsatilgan jarimalarni haqiqatan ham o'chirish (sukut bo'yicha faqat ko'rsatadi).",
        )
        parser.add_argument(
            "--faqat-nofaol",
            action="store_true",
            help="Faqat `faol=False` o'quvchilarning jarimalarini qamrab olish.",
        )

    def handle(self, *args, **options):
        ochirish = options["o'chirish"]
        faqat_nofaol = options["faqat_nofaol"]

        jarimalar = Jarima.objects.select_related(
            "berish__oquvchi", "berish__kitob"
        ).filter(tolandimi=False)

        # 1) FK butunligi buzilgan yozuvlar (berish yoki o'quvchi yo'q).
        # `berish` FK nol bo'lmagan, shuning uchun `getattr(... , None)` emas,
        # `DoesNotExist` ni ushlash kerak.
        buzilgan = []
        nofaol = []
        for jarima in jarimalar:
            try:
                oquvchi = jarima.berish.oquvchi
            except (Berish.DoesNotExist, Oquvchi.DoesNotExist):
                buzilgan.append((jarima, "berish/o'quvchi yo'q"))
                continue

            # 2) O'quvchi bor, lekin nofaol (bloklangan) — eslatma yuborilmaydi.
            if not faqat_nofaol and not oquvchi.faol:
                nofaol.append((jarima, f"oquvchi nofaol (#{oquvchi.id} {oquvchi.fish})"))

        # Ariza: tasdiqlanmagan, lekin telegram_id allaqachon boshqa
        # o'quvchiga bog'langan (eski qoldiq) yoki hech qanday o'quvchida yo'q.
        qoldiq_arizalar = []
        for ariza in Ariza.objects.filter(holati="kutmoqda"):
            mavjud = Oquvchi.objects.filter(telegram_id=ariza.telegram_id).first()
            if mavjud is None:
                qoldiq_arizalar.append(ariza)

        jami_jarima = len(buzilgan) + len(nofaol)

        if jami_jarima == 0 and not qoldiq_arizalar:
            self.stdout.write(self.style.SUCCESS("Tozalash uchun jarima topilmadi."))
            return

        self.stdout.write("")
        self.stdout.write(self.style.WARNING(f"Jami o'chiriladigan jarima: {jami_jarima}"))
        for jarima, sabab in buzilgan + nofaol:
            try:
                oquvchi_nomi = jarima.berish.oquvchi.fish
            except (Berish.DoesNotExist, Oquvchi.DoesNotExist):
                oquvchi_nomi = "(o'quvchi yo'q)"
            self.stdout.write(
                f"  [JARIMA #{jarima.id}] {jarima.summa} so'm — {sabab} ({oquvchi_nomi})"
            )

        if qoldiq_arizalar:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(f"Ro'yxatda turgan, o'quvchiga bog'lanmagan ariza: {len(qoldiq_arizalar)}")
            )
            for ariza in qoldiq_arizalar:
                self.stdout.write(f"  [ARIZA #{ariza.id}] {ariza.fish} — tg:{ariza.telegram_id}")

        if not ochirish:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "Bu faqat ko'rsatish. O'chirish uchun `--o'chirish` flagini qo'shing."
                )
            )
            return

        with transaction.atomic():
            total = 0
            if buzilgan:
                total += Jarima.objects.filter(pk__in=[j.pk for j, _ in buzilgan]).delete()[0]
            if nofaol:
                total += Jarima.objects.filter(pk__in=[j.pk for j, _ in nofaol]).delete()[0]

        self.stdout.write("")
        if total:
            self.stdout.write(self.style.SUCCESS(f"{total} ta jarima o'chirildi."))
        else:
            self.stdout.write(self.style.NOTICE("O'chiriladigan jarima topilmadi."))
        if qoldiq_arizalar:
            self.stdout.write(
                self.style.NOTICE(
                    f"({len(qoldiq_arizalar)} ta ariza saqlandi — ularni faqat kutubxonachi tasdiqlaydi.)"
                )
            )