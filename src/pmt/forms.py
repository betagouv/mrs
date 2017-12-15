from django import forms

import material

from mrsattachment.forms import MRSAttachmentWidget, MRSAttachementFormMixin


class PMTForm(MRSAttachementFormMixin, forms.Form):
    pmt = forms.FileField(
        widget=MRSAttachmentWidget(
            'pmt_upload',
            1,
        ),
        label='Préscription Médicale de Transport',
    )

    layout = material.Layout(
        material.Fieldset(
            'Votre prescription médicale',
            'pmt',
        ),
    )
