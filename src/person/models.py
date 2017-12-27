from django.db import models


class Person(models.Model):
    first_name = models.CharField(
        max_length=200,
        verbose_name='Prénom',
    )
    last_name = models.CharField(
        max_length=200,
        verbose_name='Nom de famille',
    )
    birth_date = models.DateField(
        null=True,
        verbose_name='Date de naissance',
    )
    email = models.EmailField(
        null=True,
        verbose_name='Email',
    )
    nir = models.BigIntegerField(
        verbose_name='Numéro de sécurité sociale',
    )

    class Meta:
        ordering = ('last_name', 'first_name',)
        verbose_name = 'Personne'

    def __str__(self):
        return '%s %s %s' % (self.first_name, self.last_name, self.birth_date)
