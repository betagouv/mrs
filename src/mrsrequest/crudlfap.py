import csv
from datetime import datetime
import io

from crudlfap import crudlfap

from django import forms
from django import http
from django.conf import settings
from django.core.exceptions import ValidationError

import django_tables2 as tables

from institution.models import Institution

from .views import (
    MRSRequestRejectView,
    MRSRequestProgressView,
    MRSRequestValidateView,
    MRSRequestValidateObjectsView,
)
from .models import MRSRequest


class MRSRequestListView(crudlfap.ListView):
    def get_filter_fields(self):
        filter_fields = [
            'status',
            'institution',
        ]
        if self.request.user.is_superuser:
            filter_fields.append('caisse')
        return filter_fields

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
    material_icon = 'cloud_download'
    turbolinks = False

    def get_objects(self):
        self.objects = self.queryset.filter(mandate_date=None)
        return self.objects

    def get(self, request, *args, **kwargs):
        f = io.StringIO()
        w = csv.writer(f)
        w.writerow((
            'caisse',
            'id',
            'nir',
            'naissance',
            'nom',
            'transport',
            'mandatement',
            'base',
            'montant',
            'bascule',
            'finess',
            'adeli',
        ))
        for obj in self.objects:
            date_depart = obj.transport_set.order_by(
                'date_depart'
            ).first().date_depart

            w.writerow((
                str(obj.caisse),
                obj.display_id,
                obj.insured.nir,
                obj.insured.birth_date.strftime('%d/%m/%Y'),
                '{o.first_name} {o.last_name}'.format(o=obj.insured),
                date_depart.strftime('%d/%m/%Y'),
                '',
                '',
                '',
                '',
                '',
                '',
            ))

        f.seek(0)
        response = http.HttpResponse(f.read(), content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="mrs-export-{}-{}.csv"'.format(
                getattr(settings, 'INSTANCE', 'unknown'),
                self.objects.order_by('-creation_datetime').first().display_id
            )
        )
        return response


class MRSRequestImport(crudlfap.FormMixin, crudlfap.ModelView):
    material_icon = 'cloud_upload'
    turbolinks = False
    form_invalid_message = 'Erreurs durant l\'import'
    form_valid_message = 'Importé avec succès'

    class form_class(forms.Form):
        csv = forms.FileField()

    def form_valid(self):
        def decode_utf8(input_iterator):
            for l in input_iterator:
                yield l.decode('utf-8')

        self.errors = dict()
        self.success = dict()

        f = csv.DictReader(decode_utf8(self.request.FILES['csv']))

        for i, row in enumerate(f):
            self.import_row(i, row)

        self.keys = row.keys()
        return self.render_to_response()

    def import_row(self, i, row):
        obj = self.queryset.filter(display_id=row['id']).first()

        if obj:
            self.import_obj(i, row, obj)
        else:
            self.errors[i] = dict(
                row=row,
                message='Demande introuvable en base de données'
            )

    def import_obj(self, i, row, obj):
        if row['mandatement']:
            obj.mandate_date = datetime.strptime(
                row['mandatement'],
                '%d/%m/%Y'
            ).date()

        obj.payment_base = row['base']
        obj.payment_amount = row['montant']
        obj.insured_shift = bool(row['bascule'])

        if row['finess']:
            obj.institution = self.institution_get_or_create(i, row)
            if not obj.institution:
                return

        self.save_obj(i, row, obj)

    def save_obj(self, i, row, obj):
        try:
            obj.full_clean()
        except ValidationError as e:
            self.errors[i] = dict(
                row=row,
                message=', '.join([
                    '{}: {}'.format(k, ', '.join(v))
                    for k, v in e.error_dict
                ])
            )
            return

        try:
            obj.save()
        except Exception as e:
            self.errors[i] = dict(row=row, message=e.message)
        else:
            self.success[i] = dict(object=obj, row=row)

    def institution_get_or_create(self, i, row):
        try:
            Institution(finess=row['finess']).clean_fields()
        except ValidationError as e:
            if 'finess' in e.message_dict:
                self.errors[i] = dict(
                    row=row,
                    message='FINESS invalide {}'.format(row['finess'])
                )
                return
        return Institution.objects.get_or_create(
            finess=row['finess']
        )[0]


class MRSRequestRouter(crudlfap.Router):
    model = MRSRequest
    material_icon = 'insert_drive_file'
    views = [
        MRSRequestExport,
        MRSRequestImport,
        MRSRequestValidateObjectsView,
        crudlfap.DeleteView,
        crudlfap.DetailView.clone(locks=True, title_heading=None),
        MRSRequestValidateView,
        MRSRequestRejectView,
        MRSRequestProgressView,
        MRSRequestListView,
    ]

    def allowed(self, view):
        user = view.request.user

        if not (user.is_staff or user.is_superuser):
            return False  # require superuser attribute

        if view.urlname in ('list', 'validateobjects'):
            return True  # secure by get_objects_for_user below

        if view.urlname in ('delete', 'export', 'import'):
            return user.is_superuser

        if getattr(view, 'object', None):
            if user.is_superuser:
                return True
            return view.object.caisse in user.caisses.all()

    def get_objects_for_user(self, user, perms):
        if not (user.is_staff or user.is_superuser):
            return self.model.objects.none()

        if user.is_superuser:
            qs = self.model.objects.all()
        else:
            qs = self.model.objects.filter(caisse__in=user.caisses.all())

        if 'mrsrequest.inprogress_mrsrequest' in perms:
            qs = qs.status('new')
        elif 'mrsrequest.validate_mrsrequest' in perms:
            qs = qs.status('inprogress')
        elif 'mrsrequest.reject_mrsrequest' in perms:
            qs = qs.filter(status__in=(
                self.model.STATUS_NEW, self.model.STATUS_INPROGRESS
            ))

        return qs

MRSRequestRouter(namespace='mrsrequestrouter').register()
