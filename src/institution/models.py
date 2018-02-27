import uuid

from django.core.exceptions import ValidationError
from django.db import models


def institution_finess(value):
    if value < 310000000:
        raise ValidationError('9 chiffres, doit commencer par 310')


class Institution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    finess = models.IntegerField(validators=[institution_finess])
    origin = models.CharField(
        max_length=255,
        help_text='URI du site patients'
    )

    class Meta:
        ordering = ['finess']
        verbose_name = 'Établissement'

    def __str__(self):
        return str(self.finess)
