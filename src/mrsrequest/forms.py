from django import forms
from django.views import generic

import material

from mrsattachment.forms import MRSAttachmentField

from .models import Bill, MRSRequest, PMT


class MRSRequestFormMixin(object):
    @classmethod
    def factory(cls, view, *args, **kwargs):
        if not isinstance(view, generic.View):
            raise Exception('First argument should be View instance')

        # Create a form subclass with the view instance
        cls = type(cls.__name__, (cls,), dict(view=view))

        kwargs.setdefault(
            'prefix', '{}'.format(cls.__name__.lower())
        )

        # The above made self.view available in the constructor
        form = cls(*args, **kwargs)

        for name, field in form.fields.items():
            # Joy
            form.fields[name].view = view
            form.fields[name].widget.view = view

        return form


class MRSRequestForm(MRSRequestFormMixin, forms.ModelForm):
    pmt = MRSAttachmentField(
        PMT,
        'mrsrequest:pmt_upload',
        'mrsrequest:pmt_download',
        1,
        label='Prescription Médicale de Transport obligatoire',
        help_text='Joindre le volet 2 de votre PMT fournie par votre médecin.'
    )

    bills = MRSAttachmentField(
        Bill,
        'mrsrequest:bill_upload',
        'mrsrequest:bill_download',
        20,
        label='Justificatifs',
        required=False,
        help_text=(
            'Joindre vos justificatifs si vous avez des frais (parking, péage'
            ' ou justificatif(s) de transport en commun)'
        )
    )

    date_depart = forms.DateField(
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        initial='jj/mm/aaaa',
        label='Date de l\'aller',
        widget=forms.DateInput(
            attrs={
                'type': 'date',
            }
        )
    )

    date_return = forms.DateField(
        input_formats=['%Y-%m-%d', '%d/%m/%Y'],
        initial='jj/mm/aaaa',
        label='Date de retour',
        widget=forms.DateInput(
            attrs={
                'type': 'date',
            }
    )

    layouts = dict(
        top=material.Layout(
            material.Fieldset(
                'Votre prescription médicale',
                'pmt',
            ),
        ),
        bottom=material.Layout(
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
    )

    def clean(self):
        cleaned_data = super().clean()

        date_depart = cleaned_data.get('date_depart')
        date_return = cleaned_data.get('date_return')
        if date_depart and date_return and date_depart > date_return:
            self.add_error(
                'date_return',
                'La date de retour doit être égale ou postérieure à la'
                ' date aller',
            )

        expense = cleaned_data.get('expense')
        bills = cleaned_data.get('bills')

        if expense and not bills:
            self.add_error(
                'bills',
                'Merci de soumettre vos justificatifs de transport'
            )

        return cleaned_data

    class Meta:
        model = MRSRequest
        fields = [
            'distance',
            'expense',
        ]


class CertifyForm(forms.Form):
    CERTIFY_LABEL = ("J'atteste sur l'honneur l'exactitude des renseignements"
                     " portés ci-dessus")

    certify = forms.ChoiceField(
        choices=[(True, CERTIFY_LABEL)],
        label='Validation de la demande de remboursement',
        widget=forms.RadioSelect(),
        required=True,
    )
