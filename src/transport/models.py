from django.db import models
from django.urls import reverse

from mrsattachment.models import MRSAttachment, MRSAttachmentField
from mrsrequest.models import MRSRequest


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
    distance = models.IntegerField(
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
            filename=str(upload),
            defaults=dict(
                binary=MRSAttachment.get_upload_body(upload),
            )
        )[0]


class Bill(MRSAttachment):
    transport = models.ForeignKey(
        'Transport',
        on_delete=models.CASCADE,
    )
    binary = MRSAttachmentField(
        'transport:bill_upload',
        'transport:bill_download',
        'transport:bill_destroy',
        verbose_name='Justificatif de Transport',
    )

    objects = BillManager()

    class Meta:
        ordering = ['transport', 'id']
        verbose_name = 'Justificatif'

    def get_delete_url(self):
        return reverse('transport:bill_destroy', args=[self.pk])
