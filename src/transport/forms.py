from django import forms
import material

from mrsattachment.forms import MRSAttachmentField
from mrsrequest.forms import MRSRequestFormMixin

from .models import Transport


class TransportForm(MRSRequestFormMixin, forms.ModelForm):
    bills = MRSAttachmentField(
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

        return cleaned_data

    class Meta:
        model = Transport
        fields = [
            'date_depart',
            'date_return',
            'distance',
            'expense',
        ]
