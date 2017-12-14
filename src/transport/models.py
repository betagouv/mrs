from django.db import models

from mrsrequest.models import MRSAttachement


class Transport(models.Model):
    mrsrequest = models.ForeignKey(
        'mrsrequest.MRSRequest',
        on_delete=models.CASCADE,
    )

    date_depart = models.DateField(verbose_name='Date d\'aller')
    date_return = models.DateField(verbose_name='Date de retour')
    distance = models.IntegerField('Kilométrage total parcouru')

    expense = models.DecimalField(
        decimal_places=2, max_digits=6,
        blank=True, default=0,
        verbose_name='Montant total des frais (parking et/ ou péage)'
    )

    class Meta:
        ordering = ['mrsrequest']


class Bill(MRSAttachement):
    transport = models.ForeignKey(
        'Transport',
        on_delete=models.CASCADE,
    )
    binary = models.BinaryField(
        verbose_name='Justificatif de Transport')

    class Meta:
        ordering = ['transport', 'id']
        verbose_name = 'Justificatif'
