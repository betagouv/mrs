from django import forms
from django.utils.timezone import now

import material

from mrsrequest.forms import MRSRequestFormMixin

from .models import Person


class PersonForm(MRSRequestFormMixin, forms.ModelForm):
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
