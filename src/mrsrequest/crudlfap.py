from crudlfap import crudlfap

import django_tables2 as tables

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


class MRSRequestRouter(crudlfap.Router):
    model = MRSRequest
    material_icon = 'insert_drive_file'
    views = [
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

        if view.urlname == 'delete':
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
