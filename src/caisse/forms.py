from django import forms
from django.forms.models import ModelChoiceIterator
from django.db.models import Q

from .models import Caisse, Email, Region


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
