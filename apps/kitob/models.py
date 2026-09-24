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