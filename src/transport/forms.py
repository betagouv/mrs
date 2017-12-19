from django import forms
import material

from mrsattachment.forms import MRSAttachmentWidget, MRSAttachementFormMixin

from .models import Transport


class TransportForm(MRSAttachementFormMixin, forms.ModelForm):
    bills = forms.FileField(
        widget=MRSAttachmentWidget(
            'transport:bill_upload',
            'transport:bill_download',
            20,
        ),
        label='Justificatifs',
        help_text=(
            'Joindre vos justificatifs (parking, péage ou '
            'justificatif(s) de transport en commun)'
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

    class Meta:
        model = Transport
        fields = [
            'date_depart',
            'date_return',
            'distance',
            'expense',
            'bills',
        ]
