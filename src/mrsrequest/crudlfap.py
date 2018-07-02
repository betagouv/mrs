from chardet.universaldetector import UniversalDetector
import csv
from datetime import datetime
import io
import logging

from crudlfap import crudlfap

from django import forms
from django import http
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

import django_tables2 as tables

from institution.models import Institution

from .views import (
    MRSRequestRejectView,
    MRSRequestProgressView,
    MRSRequestValidateView,
    MRSRequestValidateObjectsView,
)
from .models import MRSRequest

logger = logging.getLogger(__name__)


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
    menus = []

    def get_objects(self):
        self.objects = self.queryset.filter(
            mandate_date=None,
        ).status('validated')
        return self.objects

    def get(self, request, *args, **kwargs):
        f = io.TextIOWrapper(io.BytesIO(), encoding='utf8')
        w = csv.writer(f, delimiter=';')
        w.writerow((
            'caisse',
            'id',
            'nir',
            'naissance',
            'nom',
            'prenom',
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
                obj.insured.last_name,
                obj.insured.first_name,
                date_depart.strftime('%d/%m/%Y'),
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
                'attachment; filename="mrs-export-{}.csv"'.format(
                    getattr(settings, 'INSTANCE', 'unknown'),
                )
            )
        else:
            response = self.render_to_response()
        return response


class MRSRequestImport(crudlfap.FormMixin, crudlfap.ModelView):
    material_icon = 'cloud_upload'
    turbolinks = False
    form_invalid_message = 'Erreurs durant l\'import'
    form_valid_message = 'Importé avec succès'
    body_class = 'full-width'
    menus = []

    class form_class(forms.Form):
        csv = forms.FileField()

    def form_valid(self):
        detector = UniversalDetector()
        for line in self.request.FILES['csv'].readlines():
            detector.feed(line)
            if detector.done:
                break
        detector.close()

        def decode_utf8(input_iterator):
            for l in input_iterator:
                yield l.decode(detector.result['encoding'])

        self.errors = dict()
        self.success = dict()

        f = csv.DictReader(
            decode_utf8(self.request.FILES['csv']),
            delimiter=';'
        )

        objects = []
        for i, row in enumerate(f):
            obj = self.import_row(i, row)
            if obj:
                objects.append(obj)

        self.update_stats(objects)

        self.keys = row.keys()
        return self.render_to_response()

    def update_stats(self, objects):
        from mrsstat.models import Stat

        dates = []
        caisses = []
        institutions = []

        for obj in objects:
            if obj.creation_datetime.date() not in dates:
                dates.append(obj.creation_datetime.date())
            if obj.caisse not in caisses:
                caisses.append(obj.caisse)
            if obj.institution not in institutions:
                institutions.append(obj.institution)

        stats = Stat.objects.filter(
            date__in=dates,
        ).filter(
            Q(
                caisse__in=caisses,
            ) | Q(
                institution__in=institutions,
            )
        ).distinct()

        # update existing stats
        for stat in stats:
            logger.info('Refresh stat: {}'.format(stat))
            stat.save()

        for date in dates:
            # create missing
            Stat.objects.create_missing_for_date(
                date,
                caisses,
                institutions
            )

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
        self.update_insured(i, obj, row)
        if self.update_institution(i, obj, row) is False:
            return

        self.save_obj(i, row, obj)
        return obj

    def update_mrsrequest(self, i, obj, row):
        if row['mandatement']:
            obj.mandate_date = datetime.strptime(
                row['mandatement'],
                '%d/%m/%Y'
            ).date()

        if row['base']:
            obj.payment_base = row['base'].replace(',', '.')

        if row['montant']:
            obj.payment_amount = row['montant'].replace(',', '.')

        if row['adeli'] != '':
            obj.adeli = row['adeli']

        if row['bascule'] != '':
            shift = bool(row['bascule'])
            if obj.insured_shift != shift:
                obj.insured_shift = shift

    def update_insured(self, i, obj, row):
        if row['bascule'] != '':
            shifted = bool(row['bascule'])
            if obj.insured.shifted != shifted:
                obj.insured.shifted = shifted
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
