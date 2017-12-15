from django import forms

import material

from mrsrequest.forms import MRSRequestFormMixin


class InsuredForm(MRSRequestFormMixin, forms.Form):
    nir = forms.IntegerField(
        label='Numéro de Sécurité Sociale (sans la cléf)',
        help_text='Les 13 chiffres de votre carte vitale ou attestation',
    )
    email = forms.EmailField(
        label='Votre email',
    )

    layout = material.Layout(
        material.Fieldset(
            'Identité de l\'assuré',
            material.Row(
                'nir',
                'email',
            )
        ),
    )


class TransportedForm(MRSRequestFormMixin, forms.Form):
    first_name = forms.CharField(
        label='Prénom',
        max_length=100,
    )
    last_name = forms.CharField(
        label='Nom',
        max_length=100,
    )
    birth_date = forms.DateField(
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
    )
