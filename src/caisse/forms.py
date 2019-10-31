from django import forms
from django.forms.models import ModelChoiceIterator
from django.db.models import Q

from .models import Caisse, Email, Region


class OtherModelChoiceIterator(ModelChoiceIterator):
    def __iter__(self):
        for item in super().__iter__():
            yield item
        yield ('other', 'Autre')

    def __len__(self):
        return super().__len__() + 1


class ActiveCaisseChoiceField(forms.ModelChoiceField):

    def __init__(self, otherchoice, *args, **kwargs):
        if otherchoice:
            self.iterator = OtherModelChoiceIterator
        super().__init__(
            Caisse.objects.filter(active=True).prefetch_related('regions'),
            *args,
            **kwargs)

    def to_python(self, value):
        return value if value == 'other' else super().to_python(value)

    def validate(self, value):
        return True if value == 'other' else super().validate(value)


class ActiveRegionChoiceField(forms.ModelChoiceField):
    iterator = OtherModelChoiceIterator

    def __init__(self, *args, **kwargs):
        super().__init__(
            Region.objects.filter(caisse__active=True).distinct(),
            *args,
            **kwargs
        )

    def to_python(self, value):
        return value if value == 'other' else super().to_python(value)

    def validate(self, value):
        return True if value == 'other' else super().validate(value)


class CaisseVoteForm(forms.Form):
    region = forms.ModelChoiceField(
        Region.objects.filter(
            Q(caisse__active=False) | Q(caisse=None)).distinct(),
        label='Sélectionnez votre région dans la liste',
        required=False,
    )
    caisse = forms.ModelChoiceField(
        Caisse.objects.filter(active=False).prefetch_related('regions'),
        label='Sélectionnez votre caisse ou votre régime d\'Assurance Maladie',
        required=True,
    )
    email = forms.EmailField(
        label='Votre email',
        help_text='Nous vous informerons quand cette caisse ouvrira.',
        required=False,
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', None)

        if email and Email.objects.filter(email=email):
            raise forms.ValidationError('Email déjà enregistré')

        return email


class CaisseForm(forms.ModelForm):
    class Meta:
        model = Caisse
        fields = (
            'code',
            'name',
            'number',
            'regions',
            'liquidation_email',
            'active',
            'parking_enable',
        )
