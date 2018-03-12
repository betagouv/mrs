from django.db import models


class Caisse(models.Model):
    code = models.CharField(max_length=9)
    name = models.CharField(
        verbose_name='nom',
        max_length=50,
    )
    number = models.PositiveIntegerField(
        verbose_name='numéro',
    )
    liquidation_email = models.EmailField(
        verbose_name='email vers les liquidateureuses',
        blank=True,
        null=True
    )
    active = models.BooleanField(
        verbose_name='activé',
        default=False,
    )

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.name
