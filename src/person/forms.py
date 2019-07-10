from django import forms
from django.utils.timezone import now

import material

from mrs.forms import DateField

from .models import Person


class PersonForm(forms.ModelForm):
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

    def clean_birth_date(self):
        data = self.cleaned_data['birth_date']
        if data and (now().date() - data).days < 0:
            raise forms.ValidationError(
                'Doit être antèrieure à la date du jour')
        return data

    def get_or_create(self):
        # Return existing person untouched if possible
        # Case of twins : we added a unicity check
        # with the person's first name
        person = Person.objects.filter(
            birth_date=self.cleaned_data['birth_date'],
            nir=self.cleaned_data['nir'],
            first_name=self.cleaned_data['first_name']
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
