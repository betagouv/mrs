from django.db import models
from django.urls import reverse

from mrsrequest.models import MRSAttachement


class PMT(MRSAttachement):
    mrsrequest = models.ForeignKey(
        'mrsrequest.MRSRequest',
        on_delete=models.CASCADE,
    )
    binary = models.BinaryField(
        verbose_name='Prescription Médicale de Transport')

    def get_delete_url(self):
        return reverse('pmt_delete', args=[self.pk])

    class Meta:
        ordering = ['mrsrequest', 'id']
