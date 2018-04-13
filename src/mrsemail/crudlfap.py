from crudlfap import crudlfap

from django.db.models import Count

import django_tables2 as tables

from .models import EmailTemplate


class EmailTemplateListView(crudlfap.FilterTables2ListView):
    table_sequence = (
        'name',
        'subject',
        'requests',
        'active',
    )

    table_columns = dict(
        requests=tables.Column(
            accessor='requests',
            verbose_name='Demandes',
            order_by=['requests'],
        )
    )

    def get_queryset(self):
        return super().get_queryset().annotate(requests=Count('mrsrequest'))


crudlfap.Router(
    EmailTemplate,
    material_icon='mail',
    views=[
        EmailTemplateListView,
        crudlfap.CreateView,
        crudlfap.UpdateView,
    ]
).register()
