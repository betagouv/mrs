from django import forms

import material

from mrsattachment.forms import MRSAttachementFormMixin
from .models import PMT


class PMTForm(MRSAttachementFormMixin, forms.ModelForm):
    layout = material.Layout(
        material.Fieldset(
            'Votre prescription médicale',
            'binary',
        ),
    )

    class Meta:
        model = PMT
        fields = ['binary']
