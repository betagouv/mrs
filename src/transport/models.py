from django.db import models


class Transport(models.Model):
    prescription = models.FileField(
        verbose_name='Prescription Médicale de Transport')

    transported = models.ForeignKey(
        'person.Person',
        null=True,
        on_delete=models.SET_NULL,
        related_name='transported_transport_set',
    )
    insured = models.ForeignKey(
        'person.Person',
        null=True,
        on_delete=models.SET_NULL,
        related_name='insured_transport_set',
    )
    # Should this être back et forth ? osef :D
    aller_date = models.DateField(verbose_name='Date d\'aller')
    retour_date = models.DateField(verbose_name='Date de retour')
    distance = models.IntegerField('Kilométrage total parcouru')
    frais = models.DecimalField(
        decimal_places=2, max_digits=6,
        blank=True, default=0,
        verbose_name='Montant total des frais (parking et/ ou péage)'
    )
