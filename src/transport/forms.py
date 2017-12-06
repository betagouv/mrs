from django import forms

from .models import Transport


class TransportCreateForm(forms.ModelForm):
    CERTIFY_LABEL = ("J'atteste sur l'honneur l'exactitude des renseignements"
                     " portés ci-dessus")

    transported_first_name = forms.CharField(max_length=100)
    transported_last_name = forms.CharField(max_length=100)
    transported_birth_date = forms.DateField()

    insured_nir = forms.IntegerField()
    insured_email = forms.EmailField()

    certify = forms.ChoiceField(
        choices=[(True, CERTIFY_LABEL)],
        label='Validation de la demande de remboursement',
    )

    class Meta:
        model = Transport
        fields = (
            'prescription',
            'aller_date',
            'retour_date',
            'distance',
            'frais',
        )
