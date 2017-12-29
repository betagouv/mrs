from django.db import models
from django.urls import reverse

from mrsattachment.models import MRSAttachment


class Transport(models.Model):
    mrsrequest = models.ForeignKey(
        'mrsrequest.MRSRequest',
        on_delete=models.CASCADE,
    )

    date_depart = models.DateField(
        verbose_name='Aller',
        help_text='Date du trajet aller',
        null=True
    )
    date_return = models.DateField(
        verbose_name='Retour',
        help_text='Date du trajet retour',
        null=True
    )
    distance = models.PositiveIntegerField(
        verbose_name='Distance (km)',
        help_text='Kilométrage total parcouru',
        null=True
    )

    expense = models.DecimalField(
        decimal_places=2, max_digits=6,
        blank=True, default=0,
        verbose_name='Montant total des frais',
        help_text=(
            'Parking et/ou péage ou '
            'justificatif(s) de transport en commun'
        )
    )

    class Meta:
        ordering = ['mrsrequest']


class Bill(MRSAttachment):
    # This field serves as relation and set in MRSRequestCreateView.save()
    transport = models.ForeignKey(
        'Transport',
        null=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ['transport', 'id']
        verbose_name = 'Justificatif'

    def unlink(self):
        self.transport = None

    def get_delete_url(self):
        return reverse('transport:bill_destroy', args=[self.pk])

    def get_download_url(self):
        return reverse('transport:bill_download', args=[self.pk])
