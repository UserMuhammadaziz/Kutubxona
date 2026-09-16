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

    nomi = models.CharField(max_length = 300,  db_index=True)
    muallif = models.CharField(max_length=150, db_index=True)
    isbn = models.CharField(max_length = 20, unique=True)
    janr = models.CharField(max_length = 60, choices = JANR_CHOICES)
    nashr_yili = models.PositiveSmallIntegerField(validators=[
        MinValueValidator(1400),
        MaxValueValidator(date.today().year),
    ])
    nashriyot = models.CharField(max_length = 150, blank=True)
    tavsif = models.TextField(blank=True)
    qoshilgan_sana = models.DateField(auto_now_add=True)