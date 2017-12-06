from django.contrib.auth.models import User

from django.db import models


class Person(User):
    birth_date = models.DateField()

    # Should this be a many to many to keep track of hold records ?
    nir = models.ForeignKey(
        'NIR',
        null=True,
        on_delete=models.SET_NULL
    )


class NIR(models.Model):
    number = models.IntegerField()
