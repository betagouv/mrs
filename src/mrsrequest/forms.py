from decimal import Decimal

from django import forms
from django.core import validators
from django.utils.datastructures import MultiValueDict

import material

from caisse.forms import ActiveCaisseChoiceField
from mrs.forms import DateField
from mrsattachment.forms import MRSAttachmentField

from .models import BillATP, BillVP, MRSRequest, PMT


class MRSRequestCreateForm(forms.ModelForm):
    # do not trust this field, it's used for javascript and checked
    # by the view for permission against the request session, but is
    # NOT to be trusted as input: don't use data['mrsrequest_uuid'] nor
    # cleaned_data['mrsrequest_uuid'], you've been warned.
    mrsrequest_uuid = forms.CharField(widget=forms.HiddenInput, required=False)

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

    billvps = MRSAttachmentField(
        BillVP,
        'mrsrequest:billvp_upload',
        'mrsrequest:bill_download',
        20,
        label='Justificatifs',
        required=False,
        help_text=(
            'Joindre vos justificatifs de péage'
            ' <span data-parking-enable>'
            ' / stationnement'
            ' </span>'
            ' / transport en commun'
        )
    )

    billatps = MRSAttachmentField(
        BillATP,
        'mrsrequest:billatp_upload',
        'mrsrequest:bill_download',
        20,
        label='Justificatifs',
        required=False,
        help_text=(
            'Joindre vos justificatifs de'
            ' transport en commun'
        )
    )

    caisse = ActiveCaisseChoiceField(
        label='Votre caisse de rattachement',
    )

    parking_expensevp = forms.DecimalField(
        decimal_places=2,
        max_digits=6,
        validators=[validators.MinValueValidator(Decimal('0.00'))],
        label='Frais de parking',
        help_text='Somme totale des frais de parking (en € TTC)',
        required=False,
    )

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
        modevp=material.Layout(
            'modevp',
        ),
        vp_form=material.Layout(
            material.Row(
                'distancevp',
            ),
            material.Row(
                'expensevp',
                'parking_expensevp',
            ),
            'billvps',
        ),
        modeatp=material.Layout(
            'modeatp',
        ),
        atp_form=material.Layout(
            'expenseatp',
            'billatps',
        ),
    )

    class Meta:
        model = MRSRequest
        fields = [
            'caisse',
            'expenseatp',
            'expensevp',
            'distancevp',
            'modevp',
            'modeatp',
        ]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('initial', {})
        initial = kwargs['initial']

        kwargs['initial'].setdefault('parking_expensevp', 0)

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

    def clean(self):
        cleaned_data = super().clean()

        vp = cleaned_data.get('modevp')
        atp = cleaned_data.get('modeatp')

        if not vp and not atp:
            self.add_error(
                'modeatp',
                'Merci de choisir véhicule personnel et / ou transports en'
                ' commun',
            )
            self.add_error(
                'modevp',
                'Merci de choisir véhicule personnel et / ou transports en'
                ' commun',
            )

        if vp:
            distancevp = cleaned_data.get('distancevp')
            if not distancevp:
                self.add_error(
                    'distancevp',
                    'Merci de saisir la distance du trajet',
                )

            expensevp = cleaned_data.get('expensevp')
            parking_expensevp = cleaned_data.get('parking_expensevp')
            billvps = cleaned_data.get('billvps')
            if (expensevp or parking_expensevp) and not billvps:
                self.add_error(
                    'billvps',
                    'Merci de soumettre vos justificatifs de transport'
                )

        if atp:
            billatps = cleaned_data.get('billatps')
            if not billatps:
                self.add_error(
                    'billatps',
                    'Merci de fournir les justificatifs de transport',
                )

            expenseatp = cleaned_data.get('expenseatp')
            if not expenseatp:
                self.add_error(
                    'expenseatp',
                    'Merci de saisir le total du coût de transports en commun',
                )

        return cleaned_data

    def data_attachments(self, data, files, mrsrequest_uuid):
        pmt = PMT.objects.recorded_uploads(mrsrequest_uuid).last()
        if pmt:
            data['pmt'] = [pmt]
        else:
            data['pmt'] = []

        data['billvps'] = BillVP.objects.recorded_uploads(mrsrequest_uuid)
        data['billatps'] = BillATP.objects.recorded_uploads(mrsrequest_uuid)

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
        if self.cleaned_data.get('parking_expensevp', None):
            self.instance.expensevp += self.cleaned_data.get('parking_expensevp')

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


class TransportForm(forms.Form):
    date_depart = DateField(label='Date de l\'aller')
    date_return = DateField(label='Date de retour', required=False)

    layout = material.Layout(
        material.Row(
            'date_depart',
            'date_return',
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

        return cleaned_data


TransportFormSet = forms.formset_factory(TransportForm)


class TransportIterativeForm(forms.Form):
    iterative_show = forms.BooleanField(
        label='Avez-vous des transports itératifs à déclarer ?',
        widget=forms.CheckboxInput,
        required=False,
        help_text='Les transports itératifs sont des transports'
                  ' réguliers de distance identique (même lieu de'
                  ' départ, même lieu d\'arrivée)',
    )
    iterative_number = forms.IntegerField(
        label='Combien de trajets itératifs ?',
        initial=1,
        required=False,
    )
    trip_kind = forms.ChoiceField(
        label='',
        choices=(
            ('return', 'Aller retour'),
            ('simple', 'Aller simple'),
        ),
        widget=forms.RadioSelect,
    )

    layout = material.Layout(
        material.Fieldset(
            'Informations sur le transport',
            'trip_kind',
            'iterative_show',
            'iterative_number',
        ),
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('initial', {})
        kwargs['initial'].setdefault('trip_kind', 'return')
        super().__init__(*args, **kwargs)


class CertifyForm(forms.Form):
    CERTIFY_LABEL = ("J'atteste sur l'honneur l'exactitude des renseignements"
                     " portés ci-dessus")

    certify = forms.ChoiceField(
        choices=[(True, CERTIFY_LABEL)],
        label='Validation de la demande de remboursement',
        widget=forms.RadioSelect(),
        required=True,
    )


class UseEmailForm(forms.Form):
    USE_EMAIL_LABEL = ("En cochant cette case, vous acceptez que "
                       "Mes Remboursements Simplifiés mémorise et utilise "
                       "votre adresse email dans le but de vous envoyer occasionnellement "
                       "des emails d'informations. "
                       "Vous pouvez à tout moment vous désinscrire de ce service.")

    use_email = forms.BooleanField(
        label=USE_EMAIL_LABEL,
        widget=forms.CheckboxInput(),
        required=False,
    )


class MRSRequestForm(forms.ModelForm):
    class Meta:
        model = MRSRequest
        fields = []
