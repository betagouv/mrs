from django import forms
from django.forms.models import ModelChoiceIterator

from .models import Caisse, Email


class OtherModelChoiceIterator(ModelChoiceIterator):
    def __iter__(self):
        for item in super().__iter__():
            yield item
        yield ('other', 'Autre')

    def __len__(self):
        return super().__len__() + 1


class ActiveCaisseChoiceField(forms.ModelChoiceField):
    iterator = OtherModelChoiceIterator

    def __init__(self, *args, **kwargs):
        super().__init__(Caisse.objects.filter(active=True), *args, **kwargs)

    def to_python(self, value):
        return value if value == 'other' else super().to_python(value)

    def validate(self, value):
        return True if value == 'other' else super().validate(value)


class CaisseVoteForm(forms.Form):
    caisse = forms.ModelChoiceField(
        Caisse.objects.filter(active=False),
        label='Votre caisse d\'assurance maladie',
        required=True,
    )
    email = forms.EmailField(
        label='Votre email',
        help_text='Nous vous informerons quand cette caisse ouvrira',
        required=False,
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', None)

        if email and Email.objects.filter(email=email):
            raise forms.ValidationError('Email déjà enregistré')

        return email
