from django import forms
from django.utils.timezone import now

import material

from mrs.forms import DateField

from .models import Person


class PersonForm(forms.ModelForm):
    nir = forms.IntegerField(
        label='Numéro de sécurité sociale',
        min_value=1000000000000,
        max_value=9999999999999,
    )

    birth_date = DateField(
        label='Date de naissance',
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

    def get_or_create(self):
        # Return existing person untouched if possible
        person = Person.objects.filter(
            birth_date=self.cleaned_data['birth_date'],
            nir=self.cleaned_data['nir'],
        ).first()

        if person:
            return person

        # Otherwise create a new Person
        return super().save()

    class Meta:
        model = Person
        fields = [
            'nir',
            'email',
            'first_name',
            'last_name',
            'birth_date',
        ]
