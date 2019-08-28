from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import textwrap

from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.datastructures import MultiValueDict

import material

from caisse.forms import ActiveCaisseChoiceField
from mrs.forms import DateFieldNative
from mrsattachment.forms import MRSAttachmentField

from .models import today
from .models import BillATP, BillVP, MRSRequest, PMT, Transport


PMT_HELP = '''
Joindre le volet 2 de la prescription médicale ou le volet 3 de la demande
accord préalable.
'''

PEL_HELP = '''
Le numéro de votre Prescription Médicale Electronique de Transport (PMET) est
indiqué sur l'exemplaire patient remis par votre médecin.
<a
    href="/faq#pmt"
    title="Accèdez à la FAQ"
>Où trouver votre numéro de PMET ?</a>
'''


# Custom form field allowing decimal inputs with commas instead of dots
# Quite a useful method in France, since we mainly use commas for decimal
# numbers
class AllowedCommaDecimalField(forms.DecimalField):

    # We override the to_python method to look for a comma inside the input
    # value and if found, to replace it with a standard decimal dot before
    # passing the value to the standard DecimalField.
    def to_python(self, value):

        comma_index = 0

        if value:

            # First we check if there is a comma inside the decimal input, and
            # store its position
            try:
                comma_index = value.index(',')
            except ValueError:
                pass

            # If we found a comma inside the input value, we replace it with a
            # regular dot
            if comma_index:
                value = value.replace(',', '.')

        # We finally pass the value (modified or not) to the standard
        # DecimalField
        return super(AllowedCommaDecimalField, self).to_python(value)


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
        20,
        label='Prescription Médicale de Transport obligatoire',
        help_text=PMT_HELP,
        required=False,
    )

    pmt_pel = forms.ChoiceField(
        choices=(
            ('pmt', 'PMT (Prescription Papier)'),
            ('pel', 'PMET (Prescription Électronique)'),
        ),
        initial='pmt',
        label='Avez-vous une ...',
        widget=forms.RadioSelect,
    )

    pel = forms.CharField(
        label='Numéro de Prescription Électronique',
        help_text=PEL_HELP,
        required=False,
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
            'Joindre vos justificatifs de transport en commun'
        )
    )

    caisse = ActiveCaisseChoiceField(
        label='Votre caisse de rattachement',
    )

    expenseatp = AllowedCommaDecimalField(
        decimal_places=2,
        max_digits=6,
        validators=[validators.MinValueValidator(Decimal('0.00'))],
        label='Frais de transports',
        help_text=(
            'Somme totale des frais de transport en commun (en € TTC)'
        ),
        required=False,
        widget=forms.TextInput,
    )

    expensevp_toll = AllowedCommaDecimalField(
        decimal_places=2,
        max_digits=6,
        validators=[validators.MinValueValidator(Decimal('0.00'))],
        label='Frais de péage',
        help_text=(
            'Somme totale des frais de péage (en € TTC)'
        ),
        required=False,
        widget=forms.TextInput,
    )

    expensevp_parking = AllowedCommaDecimalField(
        decimal_places=2,
        max_digits=6,
        validators=[validators.MinValueValidator(Decimal('0.00'))],
        label='Frais de stationnement',
        help_text=(
            'Somme totale des frais de stationnement (en € TTC)'
        ),
        required=False,
        widget=forms.TextInput,
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
                'pmt_pel',
            ),
            material.Row(
                'pmt',
            ),
            material.Row(
                'pel',
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
                'expensevp_toll',
                'expensevp_parking',
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
            'expensevp_parking',
            'expensevp_toll',
            'distancevp',
            'modevp',
            'modeatp',
            'pel',
        ]
        widgets = dict(
            distancevp=forms.TextInput
        )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('initial', {})
        initial = kwargs['initial']

        kwargs['initial'].setdefault('expensevp_parking', 0)
        kwargs['initial'].setdefault('expensevp_toll', 0)

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

    def cleaned_pmt_pel(self, cleaned_data):
        pmt_pel = cleaned_data.get('pmt_pel', 'pmt')

        if pmt_pel == 'pmt':
            cleaned_data.pop('pel', None)
            if not cleaned_data.get('pmt'):
                self.add_error('pmt', 'Merci de sélectionner votre PMT')

        elif pmt_pel == 'pel':
            if not cleaned_data.get('pel'):
                self.add_error('pel', 'Merci de saisir votre numéro de PMET')

    def cleaned_vp_atp(self, cleaned_data):
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

            expensevp_toll = cleaned_data.get('expensevp_toll')
            expensevp_parking = cleaned_data.get('expensevp_parking')
            billvps = cleaned_data.get('billvps')
            if (expensevp_toll or expensevp_parking) and not billvps:
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

    def clean(self):
        cleaned_data = super().clean()

        self.cleaned_pmt_pel(cleaned_data)
        self.cleaned_vp_atp(cleaned_data)

        return cleaned_data

    def data_attachments(self, data, files, mrsrequest_uuid):
        data['pmt'] = PMT.objects.recorded_uploads(mrsrequest_uuid)
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
            self.instance.expensevp += self.cleaned_data.get(
                'parking_expensevp')

        obj = super().save(commit=commit)

        def save_attachments(form, obj):
            if form.cleaned_data.get('pmt_pel') == 'pmt':
                obj.save_pmt()
            else:
                obj.delete_pmt()
            obj.save_bills()

        save_m2m = getattr(self, 'save_m2m', None)
        if save_m2m:
            def _save_m2m():
                save_attachments(self, obj)
                save_m2m()
            self.save_m2m = _save_m2m
        else:
            save_attachments(self, obj)
        return obj


def transport_date_min_validator(value):
    date_min = (datetime.now() - relativedelta(months=27)).date()
    date_min_display = f'{date_min.day}/{date_min.month}/{date_min.year}'

    msg = textwrap.dedent(f'''
    Les dates de transports ne peuvent être inférieures à 27 mois, soit le
    {date_min_display}, merci de corriger la date.
    Pour plus d'information reportez vous à la rubrique "Combien de temps pour
    demander un remboursement ?"
    '''.strip())
    if value < date_min:
        raise ValidationError(msg)


def transport_date_max_validator(value):
    date_max = today()
    date_max_display = f'{date_max.day}/{date_max.month}/{date_max.year}'

    msg = textwrap.dedent(f'''
    Les dates de transports ne peuvent être supérieures à la date du jour, soit
    le {date_max_display}, merci de corriger la date.
    '''.strip())
    if value > date_max:
        raise ValidationError(msg)


class TransportForm(forms.Form):
    date_depart = DateFieldNative(
        label='Date de l\'aller',
        required=True,
        validators=[transport_date_min_validator, transport_date_max_validator]
    )
    date_return = DateFieldNative(
        label='Date de retour',
        required=False,
        validators=[transport_date_min_validator, transport_date_max_validator]
    )

    layout = material.Layout(
        material.Row(
            'date_depart',
            'date_return',
        )
    )

    def __init__(self, *args, **kwargs):
        self.confirms = dict()
        super().__init__(*args, **kwargs)

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

    def add_confirm(self, field, kind, other):
        self.confirms.setdefault(field, dict())
        self.confirms[field].setdefault(kind, list())
        self.confirms[field][kind].append(other)

    def set_confirms(self, formset, transports):
        """Provision self.confirms"""
        self.set_confirms_formset(formset)
        self.set_confirms_queryset(transports)

    def set_confirms_queryset(self, transports):
        date_depart = self.cleaned_data.get('date_depart')
        for transport in transports:
            if date_depart != transport.date_depart:
                continue

            if transport.mrsrequest.status_in('new', 'inprogress'):
                self.add_confirm('date_depart', 'inprogress', transport)
            if transport.mrsrequest.status_in('validated'):
                self.add_confirm('date_depart', 'validated', transport)

    def set_confirms_formset(self, formset):
        for my_name in ('depart', 'return'):
            my_name = f'date_{my_name}'
            my_value = self.cleaned_data.get(my_name)

            for form_number, form in enumerate(formset.forms):
                if form is self:
                    break

                for other_name in ('depart', 'return'):
                    other_name = f'date_{other_name}'
                    other_value = form.cleaned_data[other_name]

                    if my_value == other_value:
                        self.add_confirm(
                            my_name,
                            'duplicate',
                            (form_number, other_name)
                        )

    def add_confirms(self):
        for field, confirms in self.confirms.items():
            for confirm, confirm_data in confirms.items():
                self.add_error(
                    field,
                    getattr(self, f'get_{confirm}_message')(confirm_data)
                )

    def get_duplicate_message(self, forms_fields):
        names = dict(date_depart='aller', date_return='retour')
        labels = [
            f'{names[field_name]} n° {form_number + 1}'
            for form_number, field_name in forms_fields
        ]

        msg = ['Date de trajet déjà présente dans']
        if len(labels) == 1:
            msg.append(f'le trajet {labels[0]}')
        else:
            msg += [
                'les trajets',
                ', '.join(labels[:-1]),
                'et',
                labels[-1],
            ]

        return ' '.join(msg) + '.'

    def get_verbose_transports(self, singular, plural, transports):
        mrsrequests = set([transport.mrsrequest for transport in transports])

        msg = [plural if len(mrsrequests) > 1 else singular]

        labels = [
            ' '.join([
                'du',
                mrsrequest.creation_date_normalized,
                'n°',
                str(mrsrequest.display_id),
            ])
            for mrsrequest in mrsrequests
        ]

        if len(labels) == 1:
            msg += ['demande', labels[0]]
        else:
            msg += [
                'demandes',
                ', '.join(labels[:-1]),
                'et',
                labels[-1],
            ]

        return ' '.join(msg)

    def get_inprogress_message(self, transports):
        return ' '.join([
            'Votre demande de prise en charge pour ce trajet',
            'est en cours de traitement dans',
            self.get_verbose_transports('la', 'les', transports)
        ]) + '.'

    def get_validated_message(self, transports):
        return ' '.join([
            'Ce trajet vous a été réglé lors',
            self.get_verbose_transports('de la', 'des', transports),
        ]) + '.'


class BaseTransportFormSet(forms.BaseFormSet):
    MSG_DUPLICATE = (
        'La date {form_value} est déjà utilisée sur le transport: '
    )

    def __init__(self, data=None, *args, **kwargs):
        prefix = kwargs.get('prefix', None) or self.get_default_prefix()

        if data:
            number = data.get('iterative_number', '1')
            try:
                number = int(number)
            except ValueError:
                number = 1

            number = number if number > 0 else 1

            data = data.copy()
            for i in ['total', 'initial', 'min_num', 'max_num']:
                data[f'{prefix}-{i.upper()}_FORMS'] = number

        super().__init__(data, *args, **kwargs)

        if data:
            for i, form in enumerate(self.forms, start=1):
                form.empty_permitted = False
                if data.get('trip_kind', 'return') == 'return':
                    form.fields['date_return'].required = True

                form.fields['date_depart'].label += f' {i}'
                form.fields['date_return'].label += f' {i}'

    def get_default_prefix(self):
        return 'transport'

    def add_confirms(self, nir, birth_date):
        self.set_confirms(nir, birth_date)
        # this will call add_error for every confirm which will invalidate
        # cleaned_data
        for form in self.forms:
            form.add_confirms()

    def set_confirms(self, nir, birth_date):
        dates = set()
        for form in self.forms:
            dates.add(form.cleaned_data.get('date_depart'))
            dates.add(form.cleaned_data.get('date_return'))

        transports = Transport.objects.filter(
            mrsrequest__insured__nir=nir,
            mrsrequest__insured__birth_date=birth_date,
        ).filter(
            date_depart__in=dates
        ).distinct().select_related('mrsrequest')

        for form in self.forms:
            form.set_confirms(self, transports)

    def get_confirms_count(self):
        return sum(len(form.confirms.keys()) for form in self.forms)


TransportFormSet = forms.formset_factory(
    TransportForm,
    formset=BaseTransportFormSet,
    min_num=1,
    validate_min=True,
)


class TransportIterativeForm(forms.Form):
    iterative_show = forms.BooleanField(
        label='Avez-vous des transports itératifs* à déclarer ?',
        widget=forms.CheckboxInput,
        required=False,
        help_text='*Les transports itératifs sont des transports'
                  ' réguliers de distance identique (même lieu de'
                  ' départ, même lieu d\'arrivée)',
    )
    iterative_number = forms.IntegerField(
        label='Combien de trajets itératifs ?',
        initial=1,
        required=False,
        widget=forms.TextInput,
        min_value=1,
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
                       "Mes Remboursements Simplifiés utilise "
                       "votre adresse email dans le but de vous envoyer "
                       "occasionnellement des emails d'informations. "
                       "Vous pouvez à tout moment vous désinscrire de "
                       "ce service.")

    use_email = forms.BooleanField(
        label=USE_EMAIL_LABEL,
        widget=forms.CheckboxInput(),
        required=False,
    )


class MRSRequestForm(forms.ModelForm):
    class Meta:
        model = MRSRequest
        fields = ['distancevp']
