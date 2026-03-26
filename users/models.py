from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    address = models.TextField(blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")

    class Meta:
        db_table = "users_user"

    def __str__(self):
        return self.username
