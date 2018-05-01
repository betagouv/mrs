from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    caisses = models.ManyToManyField(
        'caisse.caisse',
        null=True,
        blank=True,
    )

    class Meta(AbstractUser.Meta):
        db_table = 'auth_user'
