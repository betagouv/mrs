from django import forms

import material

from mrsrequest.forms import MRSRequestFormMixin
from .models import PMT


class PMTForm(MRSRequestFormMixin, forms.ModelForm):
    layout = material.Layout(
        material.Fieldset(
            'Votre prescription médicale',
            'binary',
        ),
    )

    class Meta:
        model = PMT
        fields = ['binary']
