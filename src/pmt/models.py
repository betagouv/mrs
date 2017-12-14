from django.db import models

from mrsrequest.models import MRSAttachement


class PMT(MRSAttachement):
    mrsrequest = models.ForeignKey(
        'mrsrequest.MRSRequest',
        on_delete=models.CASCADE,
    )
    binary = models.BinaryField(
        verbose_name='Prescription Médicale de Transport')

    class Meta:
        ordering = ['mrsrequest', 'id']
