from chardet.universaldetector import UniversalDetector
import copy
import csv
from datetime import datetime
import io
import logging

from crudlfap import shortcuts as crudlfap

from django import forms
from django import http
from django import template
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db import transaction

import django_filters

import django_tables2 as tables

from djcall.models import Caller

from institution.models import Institution

from mrsemail.crudlfap import EmailViewMixin
from person.forms import PersonForm
from person.models import Person

from .forms import (
    MRSRequestForm,
)
from .models import MRSRequest, MRSRequestLogEntry

logger = logging.getLogger(__name__)

DATE_FORMAT = '%d/%m/%Y'

CSV_COLUMNS = (
    'caisse',
    'id',
    'nir',
    'naissance',
    'transport',
    'mandatement',
    'base',
    'montant',
    'bascule',
    'finess',
    'adeli',
)


class MRSRequestContactView(EmailViewMixin,
                            crudlfap.ObjectFormView):

    allowed_groups = ['Admin', 'UPN']
    controller = 'modal'
    action = 'click->modal#open'
    template_name = 'mrsemail/form.html'
    view_label = 'Contacter'
    material_icon = 'email'
    color = 'yellow'
    menus = ['object_detail']
    emailtemplates_menu = 'contact'
    form_valid_message = 'Utilisateur contacté'
    action_flag = MRSRequestLogEntry.ACTION_CONTACT


class MRSRequestStatusMixin:
    allowed_groups = ['Admin', 'UPN']
    controller = 'modal'
    action = 'click->modal#open'

    def form_valid(self):
        args = (self.request.user, self.action_flag)
        if hasattr(self, 'object'):
            self.object.update_status(*args)
        else:
            for obj in self.object_list:
                obj.update_status(*args)
        return super().form_valid()

    def get_log_message(self):
        return self.model.get_status_label(self.action_flag)

    def get_log_data(self):
        return {}

    def log_insert(self):
        if hasattr(self, 'object_list'):
            objects = self.object_list
        else:
            objects = [self.object]

        for obj in objects:
            obj.logentries.create(
                user=self.request.user,
                comment=self.log_message,
                data=self.log_data,
                action=self.action_flag,
            )


def mail_liquidation(subject, body, mrsrequest_pk):
    mrsrequest = MRSRequest.objects.get(pk=mrsrequest_pk)
    EmailMessage(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [mrsrequest.caisse.liquidation_email],
        reply_to=[settings.TEAM_EMAIL],
        attachments=[mrsrequest.pmt.tuple()] + [
            bill.tuple() for bill in mrsrequest.bill_set.all()
        ]
    ).send()


class MRSRequestValidateMixin(MRSRequestStatusMixin):
    form_class = MRSRequestForm
    view_label = 'Valider'
    material_icon = 'check_circle'
    color = 'green'
    action_flag = MRSRequest.STATUS_VALIDATED
    short_permission_code = 'validate'

    def get_queryset(self):
        return super().get_queryset().status('inprogress')

    def mail_render(self, destination, part, mrsrequest=None):
        mrsrequest = mrsrequest or self.object
        orig_nir = mrsrequest.field_changed('nir')
        orig_birth_date = mrsrequest.field_changed('birth_date')

        tem = template.loader.get_template(
            'mrsrequest/{}_validation_mail_{}.txt'.format(
                destination, part
            )
        ).render(dict(object=mrsrequest or self.object,
                      orig_nir=orig_nir,
                      orig_birth_date=orig_birth_date)).strip()
        return tem

    def mail_insured(self, mrsrequest=None):
        mrsrequest = mrsrequest or self.object
        Caller(
            callback='djcall.django.email_send',
            kwargs=dict(
                subject=self.mail_render('insured', 'title', mrsrequest),
                body=self.mail_render('insured', 'body', mrsrequest),
                to=[(mrsrequest or self.object).insured.email],
                reply_to=[settings.TEAM_EMAIL],
            )
        ).spool('mail')

    def mail_liquidation(self, mrsrequest=None):
        mrsrequest = mrsrequest or self.object

        if mrsrequest.total_size >= 10000000:
            messages.info(
                self.request,
                f'Demande {mrsrequest.display_id}: taille PJs superieure a 10 '
                'Mega Octets, pas de mail sur la boite de liquidation'
            )
            return

        Caller(
            callback='mrsrequest.crudlfap.mail_liquidation',
            kwargs=dict(
                subject=self.mail_render('liquidation', 'title', mrsrequest),
                body=self.mail_render('liquidation', 'body', mrsrequest),
                mrsrequest_pk=mrsrequest.pk,
            )
        ).spool('mail')

        return True


class MRSRequestValidateView(MRSRequestValidateMixin, crudlfap.ObjectFormView):
    menus = ['object', 'object_detail']
    template_name = 'mrsrequest/mrsrequest_validate.html'
    body_class = 'modal-fixed-footer'

    def has_perm(self):
        if super().has_perm():
            return self.object.status == self.model.STATUS_INPROGRESS

    def get_form_valid_message(self):
        return 'Demande n°{} validée'.format(self.object.display_id)

    def form_valid(self):
        resp = super().form_valid()
        self.mail_insured()
        self.mail_liquidation()
        return resp


class MRSRequestValidateObjectsView(
        MRSRequestValidateMixin, crudlfap.ObjectsFormView):

    def get_form_valid_message(self):
        return '{} demandes validée'.format(len(self.object_list))

    def form_valid(self):
        resp = super().form_valid()
        for obj in self.object_list:
            self.mail_insured(obj)
            self.mail_liquidation(obj)
        return resp


class MRSRequestRejectView(EmailViewMixin,
                           MRSRequestStatusMixin,
                           crudlfap.ObjectFormView):

    view_label = 'Rejeter'
    material_icon = 'do_not_disturb_on'
    color = 'red'
    action_flag = MRSRequest.STATUS_REJECTED
    menus = ['object_detail']
    emailtemplates_menu = 'reject'

    def get_queryset(self):
        return super().get_queryset().filter(status__in=(
            self.model.STATUS_NEW, self.model.STATUS_INPROGRESS
        ))

    def has_perm(self):
        if super().has_perm():
            return self.object.status in (
                self.model.STATUS_NEW, self.model.STATUS_INPROGRESS
            )

    def form_valid(self):
        self.object.save()
        return super().form_valid()

    def get_form_valid_message(self):
        return 'Demande n°{} rejetée'.format(self.object.display_id)


class MRSRequestProgressView(MRSRequestStatusMixin, crudlfap.ObjectFormView):
    form_class = MRSRequestForm
    template_name = 'mrsrequest/mrsrequest_progress.html'
    view_label = 'En cours de liquidation'
    title_submit = 'Oui'
    material_icon = 'playlist_add_check'
    color = 'green'
    action_flag = MRSRequest.STATUS_INPROGRESS
    short_permission_code = 'inprogress'
    menus = ['object_detail']

    def has_perm(self):
        if super().has_perm():
            return self.object.status == self.model.STATUS_NEW

    def get_form_valid_message(self):
        return 'Demande n°{} en cours de liquidation'.format(
            self.object.display_id
        )

    def get_queryset(self):
        return super().get_queryset().status('new')


class MRSRequestListView(crudlfap.ListView):
    allowed_groups = ['Admin', 'UPN', 'Support']

    def get_filter_fields(self):
        filter_fields = [
            'status',
            'institution',
            'creation_date__gte',
            'creation_date__lte',
        ]
        if self.request.user.profile == 'admin':
            filter_fields.append('caisse')
        return filter_fields

    filterset_extra_class_attributes = dict(
        creation_date__gte=django_filters.DateFilter(
            field_name='creation_datetime',
            lookup_expr='gte',
            input_formats=[DATE_FORMAT],
            label='Date minimale',
            widget=forms.TextInput(
                attrs={
                    'class': 'crudlfap-datepicker',
                    'data-clearable': 'true',
                    'data-format': 'dd/mm/yyyy',
                },
            )
        ),
        creation_date__lte=django_filters.DateFilter(
            field_name='creation_datetime',
            lookup_expr='lte',
            input_formats=[DATE_FORMAT],
            label='Date maximale',
            widget=forms.TextInput(
                attrs={
                    'class': 'crudlfap-datepicker',
                    'data-clearable': 'true',
                    'data-format': 'dd/mm/yyyy',
                },
            ),
        ),
    )

    DISPLAY_ID_TEMPLATE = '''
    <a
        data-position="bottom"
        data-tooltip="{{ record.tooltip }}"
        class="{{ record.color }}-text tooltipped"
        href="{{ record.get_absolute_url }}"
    >{{ record.display_id }}</a>
    '''

    table_columns = dict(  # our extra columns
        display_id=tables.TemplateColumn(
            DISPLAY_ID_TEMPLATE,
        ),
        institution=tables.Column(verbose_name='Établissement'),
        first_name=tables.Column(
            accessor='insured.first_name',
            verbose_name='Prénom',
            order_by=['insured__first_name'],
        ),
        last_name=tables.Column(
            accessor='insured.last_name',
            verbose_name='Nom',
            order_by=['insured__last_name'],
        ),
        nir=tables.Column(
            accessor='insured.nir',
            verbose_name='NIR',
            order_by=['insured__nir'],
        ),
    )

    table_sequence = (
        'creation_datetime',
        'display_id',
        'first_name',
        'last_name',
        'nir',
        'status',
        'institution',
        'caisse',
    )

    search_fields = (
        'insured__first_name',
        'insured__last_name',
        'insured__email',
        'insured__nir',
        'institution__finess',
        'display_id',
        'caisse__name',
        'caisse__number',
        'caisse__code',
    )

    def get_table_meta_checkbox_column_template(self):
        return ''.join([
            '{% if record.status == record.STATUS_INPROGRESS %}',
            super().get_table_meta_checkbox_column_template(),
            '{% endif %}',
        ])

    def get_queryset(self):
        qs = super().get_queryset()
        self.queryset = qs.select_related('caisse', 'insured')
        return self.queryset


class MRSRequestExport(crudlfap.ObjectsView):
    allowed_groups = ['Admin', 'Stat']
    material_icon = 'cloud_download'
    turbolinks = False
    menus = []
    link_attributes = {'data-noprefetch': 'true'}

    def get_title_menu(self):
        return 'Export des demandes de toutes mes caisses'

    def get_objects(self):
        self.objects = self.queryset.filter(
            mandate_date=None,
        ).status(
            'validated',
        ).select_related(
            'insured',
            'caisse',
        ).prefetch_related(
            'transport_set',
        )
        return self.objects

    def get(self, request, *args, **kwargs):
        f = io.TextIOWrapper(io.BytesIO(), encoding='utf8')
        w = csv.writer(f, delimiter=';')
        w.writerow(CSV_COLUMNS)
        for obj in self.objects:
            date_depart = None
            for transport in obj.transport_set.all():
                if not date_depart or transport.date_depart < date_depart:
                    date_depart = transport.date_depart

            if date_depart is None:
                continue  # manually imported from old database

            w.writerow((
                str(obj.caisse.number),
                obj.display_id,
                obj.insured.nir,
                obj.insured.birth_date.strftime(DATE_FORMAT),
                date_depart.strftime(DATE_FORMAT),
                '',
                '',
                '',
                '',
                '',
                '',
            ))

        if len(self.objects):
            f.seek(0)
            response = http.HttpResponse(f.read(), content_type='text/csv')
            response['Content-Disposition'] = (
                f'attachment; filename="{self.filename}.csv"'
            )
        else:
            response = self.render_to_response()
        return response

    def get_filename(self):
        return f'mrs-export-{settings.INSTANCE}'


class MRSRequestExportCaisse(MRSRequestExport):
    allowed_groups = ['Admin', 'Stat']
    urlpath = 'export/<int:pk>'
    menus = []

    def get_object(self):
        return self.request.user.caisses.get(pk=self.kwargs['pk'])

    def get_title_menu(self):
        return f'Export {self.object}'

    def get_urlargs(self):
        """Return list with object's urlfield attribute."""
        return [self.object.pk]

    def get_objects(self):
        return super().get_objects().filter(caisse=self.object)

    def get_filename(self):
        return f'mrs-export-{settings.INSTANCE}-{self.object}'


class MRSRequestImport(crudlfap.FormMixin, crudlfap.ModelView):
    allowed_groups = ['Admin', 'Stat']
    material_icon = 'cloud_upload'
    turbolinks = False
    form_invalid_message = 'Erreurs durant l\'import'
    form_valid_message = 'Importé avec succès'
    body_class = 'full-width'
    menus = []

    class form_class(forms.Form):
        csv = forms.FileField()

    def preflight(self):
        self.first_line_found = None
        self.missing_columns = dict()

        detector = UniversalDetector()
        for i, line in enumerate(self.request.FILES['csv'].readlines()):
            if self.first_line_found is None:
                self.first_line_found = line.strip()
            if len(line.strip().split(b';')) != len(CSV_COLUMNS):
                self.missing_columns[i + 1] = line
            detector.feed(line)
            if detector.done:
                break
        detector.close()
        self.encoding = detector.result['encoding']

    def form_valid(self):
        self.preflight()

        self.errors = dict()
        self.success = dict()

        for number, line in self.missing_columns.items():
            self.missing_columns[number] = line.decode(self.encoding)

        self.first_line_found = self.first_line_found.decode(self.encoding)
        self.first_line_expected = ';'.join(CSV_COLUMNS)
        if self.first_line_found != self.first_line_expected:
            return self.render_to_response()

        def decode_utf8(input_iterator):
            for l in input_iterator:
                yield l.decode(self.encoding)

        f = csv.DictReader(
            decode_utf8(self.request.FILES['csv']),
            delimiter=';'
        )

        objects = []
        for i, row in enumerate(f):
            if i + 2 in self.missing_columns.keys():
                continue

            obj = self.import_row(i, row)
            if obj:
                objects.append(obj)

        self.keys = row.keys()
        return self.render_to_response()

    def import_row(self, i, row):
        try:
            int(row['id'])
        except ValueError:
            self.errors[i + 1] = dict(
                row=row,
                message='Numéro de demande invalide: {}'.format(row['id'])
            )
            return

        obj = self.queryset.filter(display_id=row['id']).first()

        if obj:
            try:
                return self.import_obj(i, row, obj)
            except Exception as e:
                self.errors[i + 1] = dict(
                    row=row,
                    object=obj,
                    message=repr(e),
                )
        else:
            self.errors[i + 1] = dict(
                row=row,
                message='Demande introuvable en base de données'
            )

    @transaction.atomic
    def import_obj(self, i, row, obj):
        self.update_mrsrequest(i, obj, row)
        if self.update_institution(i, obj, row) is False:
            return

        self.save_obj(i, row, obj)
        return obj

    def update_mrsrequest(self, i, obj, row):
        if row['mandatement']:
            obj.mandate_date = datetime.strptime(
                row['mandatement'],
                DATE_FORMAT,
            ).date()

        if row['base']:
            obj.payment_base = row['base'].replace(',', '.')

        if row['montant']:
            obj.payment_amount = row['montant'].replace(',', '.')

        if row['adeli'] != '':
            obj.adeli = row['adeli']

        if str(row['bascule'].strip()) == '1':
            obj.insured_shift = True
            if not obj.insured.shifted:
                obj.insured.shifted = True
                obj.insured.save()

    def update_institution(self, i, obj, row):
        if row['finess']:
            obj.institution = self.institution_get_or_create(i, row)
            if not obj.institution:
                return False

    def save_obj(self, i, row, obj):
        try:
            obj.full_clean()
        except ValidationError as e:
            if list(e.error_dict.keys()) == ['creation_ip']:
                '''joys of legacy data'''
            else:
                self.errors[i + 1] = dict(
                    row=row,
                    message=', '.join([
                        '{}: {}'.format(k, ', '.join([
                            e.message % e.params
                            if e.params
                            else str(e.message)
                            for e in v
                        ]))
                        for k, v in e.error_dict.items()
                    ])
                )
                return

        try:
            obj.save()
        except Exception as e:
            self.errors[i + 1] = dict(
                row=row,
                message=getattr(e, 'message', str(e)),
            )
        else:
            self.success[i + 1] = dict(object=obj, row=row)

    def institution_get_or_create(self, i, row):
        try:
            Institution(finess=row['finess']).clean_fields()
        except ValidationError as e:
            if 'finess' in e.message_dict:
                self.errors[i + 1] = dict(
                    row=row,
                    message='FINESS invalide {}'.format(row['finess'])
                )
                return
        return Institution.objects.get_or_create(
            finess=row['finess']
        )[0]


class MRSRequestUpdateView(crudlfap.UpdateView):
    allowed_groups = ['Admin', 'UPN']
    form_class = forms.modelform_factory(
        Person,
        form=PersonForm,
        fields=['nir', 'birth_date']
    )
    form_class.layout = None  # cancel out material layout

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = copy.deepcopy(self.object.insured)
        kwargs['instance'].pk = None
        return kwargs

    def form_valid(self):
        def d():
            return {
                'insured' if i == 'pk' else i: getattr(self.object.insured, i)
                for i in (
                    'nir',
                    'birth_date',
                    'pk'
                )
            }

        self.before = d()
        self.object.insured = self.form.get_or_create()
        self.after = d()

        if self.before != self.after:
            self.object.save()
            self.log_insert()
        return http.HttpResponseRedirect(self.success_url)

    def get_changed(self):
        self.changed = dict()
        for key, old in self.before.items():
            if old != self.after[key]:
                self.changed[key] = (old, self.after[key])

    def get_log_data(self):
        return dict(changed=self.changed)

    def get_log_message(self):
        changed = []
        if 'nir' in self.changed:
            changed.append('NIR')
        if 'birth_date' in self.changed:
            changed.append('Date de naissance')
        if len(changed) > 1:
            msg = 'Modification de %s' % ', '.join(changed[:-1])
            msg += f' et {changed[-1]}'
        else:
            msg = 'Modification de %s' % changed[0]
        return msg

    def log_insert(self):
        self.object.logentries.create(
            user=self.request.user,
            comment=self.log_message,
            data=self.log_data,
            action=self.object.logentries.model.ACTION_UPDATE,
        )


class MRSRequestDetailView(crudlfap.DetailView):
    locks = True
    title_heading = None
    allowed_groups = ['Admin', 'UPN', 'Support']

    def get_labels(self):
        self.labels = dict()
        f = PersonForm()
        for name, field in f.fields.items():
            self.labels[name] = field.label
        self.labels['insured'] = 'Assuré'


class MRSRequestRouter(crudlfap.Router):
    model = MRSRequest
    material_icon = 'insert_drive_file'
    views = [
        MRSRequestExport,
        MRSRequestExportCaisse,
        MRSRequestImport,
        MRSRequestValidateObjectsView,
        crudlfap.DeleteView,
        MRSRequestDetailView,
        MRSRequestContactView,
        MRSRequestValidateView,
        MRSRequestRejectView,
        MRSRequestProgressView,
        MRSRequestUpdateView,
        MRSRequestListView,
    ]

    def get_queryset(self, view):
        user = view.request.user

        if user.is_superuser or user.profile == 'admin':
            return self.model.objects.all()
        elif user.profile in ('stat', 'upn', 'support'):
            return self.model.objects.filter(
                caisse__in=view.request.user.caisses.all()
            )

        return self.model.objects.none()


MRSRequestRouter(namespace='mrsrequestrouter').register()
