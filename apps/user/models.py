from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
    ("kutubxonachi", "Kutubxonachi"),
    ("administrator", "Administrator"),
]
    username = models.CharField(max_length = 150, unique=True)
    full_name = models.CharField(max_length = 120)
    rol = models.CharField(max_length = 20, choices=ROLE_CHOICES, default="kutubxonachi")
    telefon = models.CharField(max_length = 20, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.full_name
    
