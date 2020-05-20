from django import forms

from .models import Caisse


class CaisseForm(forms.ModelForm):
    class Meta:
        model = Caisse
        fields = (
            'code',
            'name',
            'number',
            'regions',
            'liquidation_email',
            'habilitation_email',
            'active',
            'parking_enable',
            'nopmt_enable',
        )
