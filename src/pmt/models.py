from django.db import models


class PMT(models.Model):
    request = models.ForeignKey(
        'mrsrequest.MRSRequest',
        on_delete=models.CASCADE,
    )
    filename = models.CharField(max_length=255)
    document = models.BinaryField(
        verbose_name='Prescription Médicale de Transport')

    class Meta:
        ordering = ['request', 'id']
