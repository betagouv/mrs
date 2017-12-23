from django.db import models
from django.urls import reverse

from mrsattachment.models import MRSAttachment, MRSAttachmentField
from mrsrequest.models import MRSRequest


class PMTManager(models.Manager):
    def allowed_objects(self, request):
        '''Return PMT QuerySet allowed for this request.'''
        mrsrequests = MRSRequest.objects.allowed_objects(request)
        return self.model.objects.filter(mrsrequest__in=mrsrequests)

    def record_upload(self, mrsrequest, upload):
        '''Create a PMT object from the upload.'''
        return PMT.objects.update_or_create(
            mrsrequest=mrsrequest,
            defaults=dict(
                filename=str(upload),
                binary=MRSAttachment.get_upload_body(upload),
            )
        )[0]


class PMT(MRSAttachment):
    mrsrequest = models.OneToOneField(
        'mrsrequest.MRSRequest',
        on_delete=models.CASCADE,
    )
    binary = MRSAttachmentField(
        'pmt:pmt_upload',
        'pmt:pmt_download',
        'pmt:pmt_destroy',
        max_files=1,
        verbose_name='Prescription Médicale de Transport'
    )

    objects = PMTManager()

    def get_delete_url(self):
        return reverse('pmt:pmt_destroy', args=[self.pk])

    class Meta:
        ordering = ['mrsrequest', 'id']
