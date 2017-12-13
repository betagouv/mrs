from django.db import models


class Transport(models.Model):
    request = models.ForeignKey(
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
        ordering = ['request']


class Bill(models.Model):
    transport = models.ForeignKey(
        'Transport',
        on_delete=models.CASCADE,
    )
    filename = models.CharField(max_length=255)
    document = models.BinaryField(
        verbose_name='Prescription Médicale de Transport')

    class Meta:
        ordering = ['transport', 'id']
        verbose_name = 'Justificatif'
