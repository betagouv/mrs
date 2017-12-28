from django import forms
import material

from mrsattachment.forms import MRSAttachmentField
from mrsrequest.forms import MRSRequestFormMixin

from .models import Bill, Transport


class TransportForm(MRSRequestFormMixin, forms.ModelForm):
    bills = MRSAttachmentField(
        Bill,
        'transport:bill_upload',
        'transport:bill_download',
        20,
        label='Justificatifs',
        required=False,
        help_text=(
            'Joindre vos justificatifs si vous avez des frais (parking, péage'
            ' ou justificatif(s) de transport en commun)'
        )
    )

    layout = material.Layout(
        material.Fieldset(
            'Informations sur le transport',
            material.Row(
                'date_depart',
                'date_return',
                'distance',
            ),
            'expense',
            'bills',
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        expense = cleaned_data.get('expense')
        bills = cleaned_data.get('bills')

        if expense and not bills:
            self.add_error(
                'bills',
                'Merci de soumettre vos justificatifs de transport'
            )

        date_depart = cleaned_data.get('date_depart')
        date_return = cleaned_data.get('date_return')
        if date_depart and date_return and date_depart > date_return:
            self.add_error(
                'date_return',
                "La date de retour doit être postèrieure à la date de retour",
            )

        return cleaned_data

    class Meta:
        model = Transport
        fields = [
            'date_depart',
            'date_return',
            'distance',
            'expense',
        ]
