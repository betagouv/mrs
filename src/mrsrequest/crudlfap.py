from crudlfap import crudlfap

import django_tables2 as tables

from .views import MRSRequestRejectView, MRSRequestValidateView
from .models import MRSRequest


class MRSRequestListView(crudlfap.FilterTables2ListView):
    filter_fields = (
        'status',
        'institution',
        'caisse',
    )

    table_columns = dict(  # our extra columns
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

crudlfap.Router(
    MRSRequest,
    material_icon='insert_drive_file',
    views=[
        crudlfap.DeleteView,
        crudlfap.DetailView,
        MRSRequestValidateView,
        MRSRequestRejectView,
        MRSRequestListView,
    ]
).register()
