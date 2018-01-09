from django import forms
from django.utils.timezone import now

import material

from mrsrequest.forms import MRSRequestFormMixin

from .models import Person


class PersonForm(MRSRequestFormMixin, forms.ModelForm):
    nir = forms.CharField(
        label='Numéro de sécurité sociale',
        max_length=13,
        min_length=13,
    )

    birth_date = forms.DateField(
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        initial='jj/mm/aaaa',
        label='Date de naissance',
        widget=forms.DateInput(
            attrs={
                'type': 'date',
            }
        )
    )

    layout = material.Layout(
        material.Fieldset(
            'Identité de la personne transportée',
            material.Row(
                'first_name',
                'last_name',
            ),
            'birth_date',
        ),
        material.Fieldset(
            'Identité de l\'assuré',
            material.Row(
                'nir',
                'email',
            )
        ),
    )

    def clean_nir(self):
        nir = self.cleaned_data['nir']
        try:
            int(nir)
        except ValueError:
            raise forms.ValidationError(
                'Doit être composé de 13 chiffres'
            )
        return nir

    def clean_birth_date(self):
        data = self.cleaned_data['birth_date']
        if data and (now().date() - data).days < 0:
            raise forms.ValidationError(
                'Doit être antèrieure à la date du jour')
        return data

    class Meta:
        model = Person
        fields = [
            'nir',
            'email',
            'first_name',
            'last_name',
            'birth_date',
        ]
