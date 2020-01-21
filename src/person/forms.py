from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import now

import material

from mrs.forms import DateField, CharFieldNative, \
    DateFieldNativeWithoutDatepicker
from mrs.validators import name_clean

from .models import Person


class PersonForm(forms.ModelForm):
    birth_date = DateFieldNativeWithoutDatepicker(
        label='Date de naissance',
    )
    nir = CharFieldNative(
        label='Numéro de Sécurité sociale',
        help_text='<b>Si le patient transporté est mineur, indiquer '
                  'le numéro de Sécurité sociale de son parent</b>',
        max_length=13,
    )
    first_name = CharFieldNative(
        label='Prénom',
        max_length=70,
    )
    last_name = CharFieldNative(
        label='Nom de famille',
        max_length=70,
    )
    email = CharFieldNative(
        label='Adresse email',
        max_length=254,
    )

    layout = material.Layout(
        material.Fieldset(
            '',
            material.Row(
                'first_name',
                'last_name',
            ),
            'nir',
            'birth_date',
            material.Row(
                'email',
            ),
        )
    )

    def clean_birth_date(self):
        data = self.cleaned_data['birth_date']
        if data and (now().date() - data).days < 0:
            raise forms.ValidationError(
                'Doit être antèrieure à la date du jour')
        return data

    def clean_first_name(self):
        return name_clean(self.cleaned_data['first_name'])

    def clean_last_name(self):
        return name_clean(self.cleaned_data['last_name'])

    def get_or_create(self):
        # Return existing person untouched if possible
        # Case of twins : we added a unicity check
        # with the person's first name
        person = Person.objects.filter(
            birth_date=self.cleaned_data['birth_date'],
            nir=self.cleaned_data['nir'],
            first_name__iexact=self.cleaned_data['first_name']
        ).first()

        if person:
            save = False

            # Ensure legacy data containing invalid last name are fixed
            try:
                person.full_clean()
            except ValidationError as e:
                if 'last_name' in e.error_dict:
                    person.last_name = self.cleaned_data['last_name']
                    save = True

            if (
                'email' in self.cleaned_data
                and person.email != self.cleaned_data['email']
            ):
                save = True
                person.email = self.cleaned_data['email']

            if save:
                person.save()

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


class PersonFormUpdate(forms.ModelForm):
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

    def clean_first_name(self):
        return name_clean(self.cleaned_data['first_name'])

    def clean_last_name(self):
        return name_clean(self.cleaned_data['last_name'])

    def get_or_create(self):
        # Return existing person untouched if possible
        # Case of twins : we added a unicity check
        # with the person's first name
        person = Person.objects.filter(
            birth_date=self.cleaned_data['birth_date'],
            nir=self.cleaned_data['nir'],
            first_name__iexact=self.cleaned_data['first_name']
        ).first()

        if person:
            save = False

            # Ensure legacy data containing invalid last name are fixed
            try:
                person.full_clean()
            except ValidationError as e:
                if 'last_name' in e.error_dict:
                    person.last_name = self.cleaned_data['last_name']
                    save = True

            if (
                'email' in self.cleaned_data
                and person.email != self.cleaned_data['email']
            ):
                save = True
                person.email = self.cleaned_data['email']

            if save:
                person.save()

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
