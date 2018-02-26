from django import forms

from .models import CPAM


class CPAMSelect(forms.Select):
    template_name = 'cpam/select.html'


class CPAMChoiceField(forms.ModelChoiceField):
    def __init__(self, **kwargs):
        kwargs['queryset'] = CPAM.objects.all()
        kwargs['empty_label'] = 'Merci de choisir votre CPAM'
        kwargs['widget'] = CPAMSelect
        super().__init__(**kwargs)
