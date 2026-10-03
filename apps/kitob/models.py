from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date

class Kitob(models.Model):
    JANR_CHOICES = [
    ("badiiy", "Badiiy"),
    ("ilmiy", "Ilmiy"),
    ("darslik", "Darslik"),
    ("bolalar", "Bolalar"),
    ("tarixiy", "Tarixiy"),
    ("boshqa", "Boshqa"),
]

    TIL_CHOICES = [
    ("ozbek_lotin", "O'zbek tili"),
    ("ozbek_krill", "Узбек тили"),
    ("rus", "Rus tili"),
    ("ingliz", "Ingliz tili"),
    ("boshqa", "Boshqa"),
]

    HOLAT_CHOICES = [
    ("mavjud", "Mavjud"),
    # `berilgan` nusxa holatidan avtomatik hisoblanadi
    # (kitob/services.py::kitob_holatini_yenila) — qo'lda o'zgartirilmaydi.
    ("berilgan", "Berilgan"),
    ("yoqolgan", "Yo'qolgan"),
]

    nomi = models.CharField(max_length = 300,  db_index=True)
    muallif = models.CharField(max_length=150, db_index=True)
    isbn = models.CharField(max_length = 20, unique=True, null=True, blank=True)
    janr = models.CharField(max_length = 60, choices = JANR_CHOICES)
    til = models.CharField(max_length = 30, choices = TIL_CHOICES, blank=True, default="")
    narh = models.DecimalField(max_digits = 12, decimal_places = 2, null = True, blank = True)
    buyurtma_soni = models.PositiveIntegerField(null = True, blank = True)
    holati = models.CharField(max_length = 20, choices = HOLAT_CHOICES, default="mavjud")
    nashr_yili = models.PositiveSmallIntegerField(validators=[
        MinValueValidator(1400),
        MaxValueValidator(date.today().year),
    ])
    nashriyot = models.CharField(max_length = 150, blank=True)
    tavsif = models.TextField(blank=True)
    qoshilgan_sana = models.DateField(auto_now_add=True)


class BandQilish(models.Model):
    """Kitobni band qilish (saqlab qo'yish) so'rovi.

    O'quvchi yoki o'qituvchi kitobni band qilishni so'raydi — shundan keyin
    kitob **hech kimga berilmaydi**, chunki u maxsus maqsadga ajratilmoqda
    (o'qituvchi darsga tayyorlanmoqda, o'quvchi imtihonga tayyorlanmoqda
    va h.k.).

    Band qilingan kitobni faqat kutubxonachi yoki administrator tasdiqlashi
    mumkin: `tasdiqla()` chaqirilganda so'rov yaratuvchiga **Berish** yozuvi
    bilan kitob beriladi (muddat, jarima va qaytarish odatidagidek ishlaydi).
    Tasdiqlanmagan so'rov navbatni ham to'xtatadi.
    """

    HOLAT_CHOICES = [
        ("kutmoqda", "Tasdiqlash kutilmoqda"),
        ("tasdiqlandi", "Tasdiqlandi"),
        ("rad_etildi", "Rad etildi"),
        ("bekor_qilindi", "Bekor qilindi"),
    ]

    # PROTECT: band qilingan kitobni/nusxani o'chirishga yo'l yo'q.
    kitob = models.ForeignKey(
        Kitob, on_delete=models.PROTECT, related_name="band_qilishlar"
    )
    oquvchi = models.ForeignKey(
        "oquvchi.Oquvchi", on_delete=models.PROTECT, related_name="band_qilishlar"
    )
    holati = models.CharField(max_length=20, choices=HOLAT_CHOICES, default="kutmoqda")
    izoh = models.CharField(max_length=255, blank=True)
    so_rov_sanasi = models.DateTimeField(auto_now_add=True)
    # Tasdiqlagan xodim (kutubxonachi yoki administrator).
    tasdiqlovchi = models.ForeignKey(
        "user.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tasdiqlangan_bandlar",
    )
    tasdiqlash_sanasi = models.DateTimeField(null=True, blank=True)
    tasdiqlash_izohi = models.CharField(max_length=255, blank=True)
    # Tasdiqlashda yaratilgan berish yozuvi (protokol uchun).
    berish = models.OneToOneField(
        "berish.Berish", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="band_qilish",
    )

    class Meta:
        ordering = ["-so_rov_sanasi", "-id"]
        verbose_name = "Band qilish"
        verbose_name_plural = "Band qilishlar"
        indexes = [
            models.Index(fields=["holati", "-so_rov_sanasi"], name="band_holat_sana_idx"),
        ]
        constraints = [
            # Bir kitob uchun faqat bitta kutilayotgan band bo'lishi mumkin:
            # aks holda tasdiqlanishda kimga berilishi aniq bo'lmasdi.
            models.UniqueConstraint(
                fields=["kitob"],
                condition=models.Q(holati="kutmoqda"),
                name="band_kitob_bitta_kutmoqda",
            ),
        ]

    def __str__(self):
        return f"{self.kitob.nomi} — {self.oquvchi.fish} ({self.get_holati_display()})"

    @property
    def faolmi(self):
        """Tasdiqlash kutilayotgan so'rov (faqat shu holatda kitob bloklanadi)."""
        return self.holati == "kutmoqda"