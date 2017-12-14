from django import forms

import material


class MRSRequestCreateForm(forms.Form):
    CERTIFY_LABEL = ("J'atteste sur l'honneur l'exactitude des renseignements"
                     " portés ci-dessus")

    id = forms.CharField(widget=forms.HiddenInput)

    pmt = forms.FileField(
        label='Préscription Médicale de Transport',
    )

    transported_first_name = forms.CharField(
        label='Prénom',
        max_length=100,
    )
    transported_last_name = forms.CharField(
        label='Nom',
        max_length=100,
    )
    transported_birth_date = forms.DateField(
        label='Date de naissance',
    )

    insured_nir = forms.IntegerField(
        label='Numéro de Sécurité Sociale (sans la cléf)',
        help_text='Les 13 chiffres de votre carte vitale ou attestation',
    )
    insured_email = forms.EmailField(
        label='Votre email',
    )

    certify = forms.ChoiceField(
        choices=[(True, CERTIFY_LABEL)],
        label='Validation de la demande de remboursement',
        widget=forms.RadioSelect(),
    )

    date_depart = forms.DateField(
        label='Date du trajet aller',
    )
    date_return = forms.DateField(
        label='Date du trajet retour',
    )
    distance = forms.IntegerField(
        label='Kilométrage total parcouru en voiture',
    )
    expense = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        label=(
            'Montant total des frais (parking et/ou péage ou '
            'justificatif(s) de transport en commun)'
        )
    )

    layout = material.Layout(
        material.Fieldset(
            'Votre prescription médicale',
            'pmt',
        ),
        material.Fieldset(
            'Identité de la personne transportée',
            material.Row(
                'transported_first_name',
                'transported_last_name',
            ),
            'transported_birth_date',
        ),
        material.Fieldset(
            'Identité de l\'assuré',
            material.Row(
                'insured_nir',
                'insured_email',
            )
        ),
        material.Fieldset(
            'Informations sur le transport',
            material.Row(
                'date_depart',
                'date_return',
                'distance',
            ),
            'expense',
        ),
        'certify',
    )
