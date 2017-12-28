from django import forms

import material

from mrsrequest.forms import MRSRequestFormMixin
from mrsattachment.forms import MRSAttachmentField
from .models import PMT


class PMTForm(MRSRequestFormMixin, forms.Form):
    pmt = MRSAttachmentField(
        PMT,
        'pmt:pmt_upload',
        'pmt:pmt_download',
        1,
        label='Prescription Médicale de Transport obligatoire',
        help_text='Joindre votre PMT fournie par votre médecin.'
    )

    layout = material.Layout(
        material.Fieldset(
            'Votre prescription médicale',
            'pmt',
        ),
    )
