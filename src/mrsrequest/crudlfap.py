from chardet.universaldetector import UniversalDetector
import copy
import csv
import datetime
import io
import logging

from crudlfap import shortcuts as crudlfap

from django import forms
from django import http
from django import template
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

import django_filters

import django_tables2 as tables

from djcall.models import Caller

from institution.models import Institution

from mrs.settings import DATE_FORMAT_FR
from mrsemail.crudlfap import EmailViewMixin
from person.forms import PersonForm
from person.models import Person

from .forms import (
    MRSRequestForm,
)
from .models import MRSRequest, MRSRequestLogEntry

logger = logging.getLogger(__name__)

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


class MRSRequestValidateMixin(MRSRequestStatusMixin):
    fields = []
    view_label = 'Valider'
    material_icon = 'check_circle'
    color = 'green'
    action_flag = MRSRequest.STATUS_VALIDATED
    short_permission_code = 'validate'

    def get_queryset(self):
        return super().get_queryset().status('inprogress')

    def mail_render(self, destination, part, mrsrequest=None):
        mrsrequest = mrsrequest or self.object
        orig = {
            name: mrsrequest.field_changed(name)
            for name in ('nir', 'birth_date', 'distancevp')
        }

        tem = template.loader.get_template(
            'mrsrequest/{}_validation_mail_{}.txt'.format(
                destination, part
            )
        ).render(dict(object=mrsrequest or self.object,
                      orig=orig)).strip()
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
        return resp


class MRSRequestValidateObjectsView(
        MRSRequestValidateMixin, crudlfap.ObjectsFormView):

    def get_form_valid_message(self):
        return '{} demandes validée'.format(len(self.object_list))

    def form_valid(self):
        resp = super().form_valid()
        for obj in self.object_list:
            self.mail_insured(obj)
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
    fields = []
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


def boolean_gte_filter(qs, name, value):
    if value is True:
        return qs.filter(**{f'{name}__gte': 1})
    elif value is False:
        return qs.filter(**{f'{name}': 0})


class MRSRequestListView(crudlfap.ListView):
    allowed_groups = ['Admin', 'UPN', 'Support']

    def get_show_caisse_filter(self):
        self.show_caisse_filter = (
            self.request.user.caisses.count() > 1
            or self.request.user.profile == 'admin'
        )

    def get_filter_fields(self):
        filter_fields = [
            'status',
            'institution',
            'creation_date__gte',
            'creation_date__lte',
        ]
        if self.show_caisse_filter:
            filter_fields.append('caisse')
        return filter_fields

    filterset_extra_class_attributes = dict(
        creation_date__gte=django_filters.DateFilter(
            field_name='creation_datetime',
            lookup_expr='gte',
            input_formats=[DATE_FORMAT_FR],
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
            input_formats=[DATE_FORMAT_FR],
            label='Date maximale',
            widget=forms.TextInput(
                attrs={
                    'class': 'crudlfap-datepicker',
                    'data-clearable': 'true',
                    'data-format': 'dd/mm/yyyy',
                },
            ),
        ),
        has_conflicts_accepted=django_filters.BooleanFilter(
            field_name='conflicts_accepted',
            label='Signalements acceptés',
            method=boolean_gte_filter,
        ),
        has_conflicts_resolved=django_filters.BooleanFilter(
            field_name='conflicts_resolved',
            label='Signalements résolus',
            method=boolean_gte_filter,
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

    def get_table_sequence(self):
        sequence = [
            'creation_datetime',
            'display_id',
            'first_name',
            'last_name',
            'nir',
            'status',
            'institution',
            'caisse',
        ]
        if self.request.user.profile == 'admin':
            sequence.append('saving')
        return sequence

    def get_filterset(self):
        filterset = super().get_filterset() or self.filterset
        form = filterset.form
        if 'caisse' in form.fields and self.request.user.profile != 'admin':
            form.fields['caisse'].queryset = self.request.user.caisses.all()
        return filterset

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
            mandate_datevp=None,
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
                obj.insured.birth_date.strftime(DATE_FORMAT_FR),
                date_depart.strftime(DATE_FORMAT_FR),
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

        self.errors = dict()
        self.success = dict()

        for number, line in self.missing_columns.items():
            self.missing_columns[number] = line.decode(self.encoding)

        self.first_line_found = self.first_line_found.decode(self.encoding)
        self.first_line_expected = ';'.join(CSV_COLUMNS)

    def form_valid(self):
        self.preflight()

        if self.first_line_found != self.first_line_expected:
            return self.render_to_response()

        def decode_utf8(input_iterator):
            for l in input_iterator:
                yield l.decode(self.encoding).strip()

        f = csv.DictReader(
            decode_utf8(self.request.FILES['csv']),
            delimiter=';'
        )

        objects = []
        caisses = set()
        for i, row in enumerate(f):
            if i + 2 in self.missing_columns.keys():
                continue

            obj = self.import_row(i, row)
            if obj:
                objects.append(obj)
                caisses.add(obj.caisse)

        for caisse in caisses:
            caisse.import_datetime = timezone.now()
            caisse.save()

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
            obj.mandate_datevp = datetime.datetime.strptime(
                row['mandatement'],
                DATE_FORMAT_FR,
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
    extra_form_classes = dict(
        person=forms.modelform_factory(
            Person,
            form=PersonForm,
            fields=['nir', 'birth_date']
        )
    )
    extra_form_classes['person'].layout = None  # cancel out material layout

    def get_extra_forms(self):
        self.extra_forms = {
            k: v(
                *self.extra_form_args,
                **self.extra_form_kwargs[k],
            )
            for k, v in self.extra_form_classes.items()
        }

    def get_form_class(self):
        if self.object.modevp:
            self.form_class = MRSRequestForm
        else:
            self.form_class = forms.Form

    def get_extra_form_args(self):
        if self.request.method == 'POST':
            self.extra_form_args = [self.request.POST]
        else:
            self.extra_form_args = []

    def get_extra_form_kwargs(self):
        self.extra_form_kwargs = dict(person=dict())
        person = copy.deepcopy(self.object.insured)
        person.pk = None
        self.extra_form_kwargs['person']['instance'] = person

    def get_extra_forms_valid(self):
        for form in self.extra_forms.values():
            if not form.is_valid():
                return False
        return True

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        if self.form.is_valid() and self.extra_forms_valid:
            return self.form_valid()
        else:
            return self.form_invalid()

    def get_changed_fields(self):
        self.changed_fields = copy.copy(self.form.changed_data)
        for form in self.extra_forms.values():
            self.changed_fields += form.changed_data

    def get_changed_data(self):
        self.changed_data = dict()

        def add_changed_data(name, form):
            if name not in form.fields:
                return

            if isinstance(form[name].initial, datetime.date):
                self.changed_data[name] = (
                    form[name].initial,
                    form.cleaned_data[name].strftime('%d/%m/%Y')
                )
            else:
                self.changed_data[name] = (
                    form[name].initial,
                    form.cleaned_data[name]
                )

        for name in self.changed_fields:
            add_changed_data(name, self.form)

            for form in self.extra_forms.values():
                add_changed_data(name, form)

    def get_changed_labels(self):
        self.changed_labels = []

        def add_changed_labels(form):
            for name in form.changed_data:
                self.changed_labels.append(
                    form[name].label
                )

        add_changed_labels(self.form)
        for form in self.extra_forms.values():
            add_changed_labels(form)

    def form_valid(self):
        def d():
            data = {
                'insured' if i == 'pk' else i: getattr(self.object.insured, i)
                for i in (
                    'nir',
                    # 'birth_date',
                    'pk'
                )
            }
            date = getattr(self.object.insured, 'birth_date')
            if date:
                data['birth_date'] = date.strftime(DATE_FORMAT_FR)
            return data

        self.person_before = d()
        self.object.insured = self.extra_forms['person'].get_or_create()
        self.person_after = d()

        if self.changed_data:
            self.object.save()
            self.log_insert()

        return http.HttpResponseRedirect(self.success_url)

    def get_log_data(self):
        return dict(changed=self.changed_data)

    def get_log_message(self):
        if len(self.changed_labels) > 1:
            msg = 'Modification de %s' % ', '.join(self.changed_labels[:-1])
            msg += f' et {self.changed_labels[-1]}'
        else:
            msg = 'Modification de %s' % self.changed_labels[0]

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

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            'insured',
        ).prefetch_related(
            'transport_set',
        )

    def get_labels(self):
        self.labels = dict()
        f = PersonForm()
        for name, field in f.fields.items():
            self.labels[name] = field.label
        self.labels['insured'] = 'Assuré'
        self.labels['distancevp'] = 'KM parcourus VP'


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
