from django.db import models
from django.urls import reverse

from mrsattachment.models import MRSAttachment


class PMT(MRSAttachment):
    mrsrequest = models.OneToOneField(
        'mrsrequest.MRSRequest',
        null=True,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return 'PMT: {}'.format(self.mrsrequest.pk)

    def get_delete_url(self):
        return reverse('pmt:pmt_destroy', args=[self.pk])

    def get_download_url(self):
        return reverse('pmt:pmt_download', args=[self.pk])

    class Meta:
        ordering = ['mrsrequest', 'id']
