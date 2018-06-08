import uuid

from django.core.exceptions import ValidationError
from django.db import models


def institution_finess(value):
    if value < 310000000:
        raise ValidationError('9 chiffres, doit commencer par 310')


class Institution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    finess = models.IntegerField(validators=[institution_finess], unique=True)
    origin = models.CharField(
        default='',
        max_length=255,
        help_text='URI du site patients'
    )
    dynamic_allow = models.BooleanField(
        default=False,
        verbose_name='Autorisation CORS dynamique',
        help_text=(
            'Cocher pour les hebergeurs non-HDS qui ne veulent pas de controle'
            ' d\'origine'
        )
    )

    class Meta:
        ordering = ['finess']
        verbose_name = 'Établissement'

    def natural_key(self):
        return self.finess

    def __str__(self):
        return str(self.finess)
