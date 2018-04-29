from crudlfap import crudlfap

import django_tables2 as tables

from .views import (
    MRSRequestRejectView,
    MRSRequestProgressView,
    MRSRequestValidateView,
)
from .models import MRSRequest


class MRSRequestListView(crudlfap.FilterTables2ListView):
    filter_fields = (
        'status',
        'institution',
        'caisse',
    )

    DISPLAY_ID_TEMPLATE = '''
    <span
        data-position="bottom"
        data-tooltip="En attente de traitement depuis {{ record.days }} jours"
        class="{{ record.color }}-text tooltipped"
    >{{ record.display_id }}</span>
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

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('caisse', 'insured')
        return qs


class MRSRequestRouter(crudlfap.Router):
    model = MRSRequest
    material_icon = 'insert_drive_file'
    views = [
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
            return False

        if view.urlname == 'delete':
            return user.is_superuser

        if getattr(view, 'object', None):
            if user.is_superuser:
                return True
            return view.object.caisse in user.caisses.all()

        if view.urlname == 'list':
            return True

    def get_objects_for_user(self, user, perms):
        if not (user.is_staff or user.is_superuser):
            return self.model.objects.none()

        if user.is_superuser:
            return self.model.objects.all()

        return self.model.objects.filter(caisse__in=user.caisses.all())

MRSRequestRouter(namespace='mrsrequestrouter').register()
