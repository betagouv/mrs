from django.db import models
from django.urls import reverse

from mrsrequest.models import MRSAttachement, MRSRequest


class Transport(models.Model):
    mrsrequest = models.ForeignKey(
        'mrsrequest.MRSRequest',
        on_delete=models.CASCADE,
    )

    date_depart = models.DateField(
        verbose_name='Date d\'aller',
        null=True
    )
    date_return = models.DateField(
        verbose_name='Date de retour',
        null=True
    )
    distance = models.IntegerField(
        'Kilométrage total parcouru',
        null=True
    )

    expense = models.DecimalField(
        decimal_places=2, max_digits=6,
        blank=True, default=0,
        verbose_name='Montant total des frais (parking et/ ou péage)'
    )

    class Meta:
        ordering = ['mrsrequest']


class BillManager(models.Manager):
    def allowed_objects(self, request):
        return Bill.objects.filter(
            transport__mrsrequest__in=MRSRequest.objects.allowed_objects(
                request))

    def record_upload(self, mrsrequest, upload):
        '''
        Create a Bill object from the upload on the request's transport.

        When we want to support multiple forms in the future, we'll have a form
        number in the field_name attribute of the upload.
        '''
        return Bill.objects.update_or_create(
            transport=Transport.objects.get_or_create(
                mrsrequest=mrsrequest)[0],
            defaults=dict(
                filename=str(upload),
                binary=MRSAttachement.get_upload_body(upload),
            )
        )[0]


class Bill(MRSAttachement):
    transport = models.ForeignKey(
        'Transport',
        on_delete=models.CASCADE,
    )
    binary = models.BinaryField(
        verbose_name='Justificatif de Transport')

    objects = BillManager()

    class Meta:
        ordering = ['transport', 'id']
        verbose_name = 'Justificatif'

    def get_delete_url(self):
        return reverse('bill_delete', args=[self.pk])
