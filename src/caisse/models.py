from django.core.exceptions import ValidationError
from django.db import models


def validate_caisse_number(value):
    try:
        value = int(value)
    except ValueError:
        raise ValidationError('Doit etre numerique')

    if not 0 < value < 999:
        raise ValidationError('Doit etre entre 0 et 999')


class Caisse(models.Model):
    code = models.CharField(max_length=9)
    name = models.CharField(
        verbose_name='nom',
        max_length=50,
    )
    number = models.CharField(
        max_length=3,
        verbose_name='numéro',
        validators=[validate_caisse_number],
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


def caisse_number_format(sender, instance, **kwargs):
    instance.number = '{:03d}'.format(int(instance.number))
models.signals.pre_save.connect(caisse_number_format, sender=Caisse)
