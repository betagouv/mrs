import uuid

from django import forms
from django.utils.datastructures import MultiValueDict

import material

from caisse.forms import ActiveCaisseChoiceField
from mrs.forms import DateField
from mrsattachment.forms import MRSAttachmentField
from mrsemail.models import EmailTemplate

from .models import Bill, MRSRequest, PMT, Transport


class MRSRequestForm(forms.ModelForm):
    pmt = MRSAttachmentField(
        PMT,
        'mrsrequest:pmt_upload',
        'mrsrequest:pmt_download',
        1,
        label='Prescription Médicale de Transport obligatoire',
        help_text=(
            'Joindre le volet 2 de la prescription médicale '
            'ou le volet 3 de la demande accord préalable'
        )
    )

    bills = MRSAttachmentField(
        Bill,
        'mrsrequest:bill_upload',
        'mrsrequest:bill_download',
        20,
        label='Justificatifs',
        required=False,
        help_text=(
            'Joindre vos justificatifs de péage / stationnement /'
            ' transport en commun'
            ' - voir FAQ pour la liste des justificatifs acceptés'
        )
    )

    caisse = ActiveCaisseChoiceField(
        label='Votre caisse de rattachement',
    )

    # do not trust this field, it's used for javascript and checked
    # by the view for permission against the request session, but is
    # NOT to be trusted, don't use data['mrsrequest_uuid'] nor
    # cleaned_data['mrsrequest_uuid'], you've been warned.
    # Except for staff, in the admin version of the form.
    mrsrequest_uuid = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('initial', {})
        initial = kwargs['initial']

        if 'mrsrequest_uuid' in kwargs:
            mrsrequest_uuid = kwargs.pop('mrsrequest_uuid')
            instance = kwargs.get('instance')
            if not instance:
                kwargs['instance'] = MRSRequest()
            kwargs['instance'].id = mrsrequest_uuid
        elif 'instance' in kwargs:
            mrsrequest_uuid = str(kwargs['instance'].id)
        else:
            raise Exception('No instance, no uuid, secure it yourself')

        initial['mrsrequest_uuid'] = mrsrequest_uuid

        data, files, args, kwargs = self.args_extract(args, kwargs)

        if data:
            data, files = self.data_attachments(data, files, mrsrequest_uuid)

        kwargs['data'] = data
        kwargs['files'] = files
        super().__init__(*args, **kwargs)

    def data_attachments(self, data, files, mrsrequest_uuid):
        pmt = PMT.objects.recorded_uploads(mrsrequest_uuid).last()
        if pmt:
            data['pmt'] = [pmt]
        else:
            data['pmt'] = []

        data['bills'] = Bill.objects.recorded_uploads(mrsrequest_uuid)

        if files:
            files.update(data)
        else:
            files = data
        return data, files

    def args_extract(self, args, kwargs):
        """Extract data and files args, return mutable objects."""
        # make popable (can't pop tuple of args)
        args = list(args)

        def getarg(name, num):
            if args and len(args) > num:
                return args.pop(num)
            elif kwargs.get('files'):
                return kwargs.pop('files')
            return None

        # First to not affect data = args.pop(0)
        files = getarg('files', 1)
        data = getarg('data', 0)

        # make mutable if something
        if files:
            files = MultiValueDict(files)
        if data:
            data = MultiValueDict(data)

        return data, files, args, kwargs

    def save(self, commit=True):
        obj = super().save(commit=commit)
        save_m2m = getattr(self, 'save_m2m', None)
        if save_m2m:
            def _save_m2m():
                obj.save_attachments()
                save_m2m()
            self.save_m2m = _save_m2m
        else:
            obj.save_attachments()
        return obj

    class Meta:
        model = MRSRequest
        fields = [
            'caisse',
            'expense',
            'distance',
        ]


class MRSRequestAdminForm(MRSRequestForm):
    '''This form is not secure: it uses any uuid that is posted.'''

    def __init__(self, *args, **kwargs):
        data, files, args, kwargs = self.args_extract(args, kwargs)
        kwargs.setdefault('initial', {})

        instance = kwargs.get('instance')
        if instance:
            try:
                instance.pmt
            except PMT.DoesNotExist:
                pass
            else:
                kwargs['initial']['pmt'] = [instance.pmt]
            kwargs['initial']['bills'] = instance.bill_set.all()
            kwargs['initial']['mrsrequest_uuid'] = str(instance.id)
        else:
            if data and 'mrsrequest_uuid' in data:
                kwargs['mrsrequest_uuid'] = data.get('mrsrequest_uuid')
            else:
                kwargs['mrsrequest_uuid'] = str(uuid.uuid4())

        super().__init__(data, files, *args, **kwargs)

    class Meta:
        model = MRSRequest
        fields = [
            'mrsrequest_uuid',
            'expense',
            'distance',
            'insured',
        ]


class MRSRequestCreateForm(MRSRequestForm):
    layouts = dict(
        above=material.Layout(
            material.Fieldset(
                'Votre caisse d\'assurance maladie',
                'caisse',
            ),
        ),
        top=material.Layout(
            material.Fieldset(
                'Votre prescription médicale',
                'pmt',
            ),
        ),
        bottom=material.Layout(
            material.Row(
                'distance',
            ),
            'expense',
            'bills',
        )
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
        model = MRSRequest
        fields = [
            'caisse',
            'distance',
            'expense',
        ]


class TransportForm(forms.ModelForm):
    date_depart = DateField(label='Date de l\'aller')
    date_return = DateField(label='Date de retour')

    layout = material.Layout(
        material.Row(
            'date_depart',
            'date_return',
        ),
    )

    class Meta:
        model = Transport
        fields = [
            'date_depart',
            'date_return',
        ]

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

        return cleaned_data


class TransportIterativeForm(TransportForm):
    iterative_show = forms.BooleanField(
        label='Avez-vous des transports itératifs à déclarer ?',
        widget=forms.CheckboxInput,
        required=False,
    )
    iterative_number = forms.IntegerField(
        label='Combien de trajets itératifs souhaitez-vous déclarer ?',
        initial=1,
        required=False,
    )

    layout = material.Layout(
        material.Fieldset(
            'Informations sur le transport',
            material.Row(
                'date_depart',
                'date_return',
            ),
            'iterative_show',
            'iterative_number',
        ),
    )


class CertifyForm(forms.Form):
    CERTIFY_LABEL = ("J'atteste sur l'honneur l'exactitude des renseignements"
                     " portés ci-dessus")

    certify = forms.ChoiceField(
        choices=[(True, CERTIFY_LABEL)],
        label='Validation de la demande de remboursement',
        widget=forms.RadioSelect(),
        required=True,
    )


class MRSRequestRejectForm(forms.ModelForm):
    template = forms.ModelChoiceField(
        EmailTemplate.objects.active(),
        widget=forms.Select(attrs={
            'data-controller': 'emailtemplate',
            'data-action': 'change->emailtemplate#change',
        }),
    )
    subject = forms.CharField()
    body = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = MRSRequest
        fields = []

    def save(self, commit=True):
        self.instance.status = MRSRequest.STATUS_REJECTED
        if commit:
            self.instance.save()
        return self.instance


class MRSRequestValidateForm(forms.ModelForm):
    class Meta:
        model = MRSRequest
        fields = []

    def save(self, commit=True):
        self.instance.status = MRSRequest.STATUS_VALIDATED
        if commit:
            self.instance.save()
        return self.instance
