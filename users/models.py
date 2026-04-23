from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_agent = models.BooleanField(default=False, verbose_name="Я агент")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")

    def __str__(self):
        return self.username