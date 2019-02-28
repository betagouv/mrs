from crudlfap import shortcuts as crudlfap

from django.db import models

import django_tables2 as tables

from .forms import CaisseForm
from .models import Caisse, Email


class CaisseListView(crudlfap.ListView):
    table_sequence = (
        'name',
        'active',
        'score',
        'conflicts_accepted',
        'conflicts_resolved',
        'import_datetime',
    )

    conflicts_accepted_template = '''
    <a
        href="{{ record.get_conflicts_accepted_url }}"
    >{{ record.mrsrequest__conflicts_accepted__sum }}</a>
    '''

    conflicts_resolved_template = '''
    <a
        href="{{ record.get_conflicts_resolved_url }}"
    >{{ record.mrsrequest__conflicts_resolved__sum }}</a>
    '''

    table_columns = dict(
        conflicts_accepted=tables.TemplateColumn(
            conflicts_accepted_template,
            accessor='mrsrequest__conflicts_accepted__sum',
            verbose_name='Signalements confirmés',
        ),
        conflicts_resolved=tables.TemplateColumn(
            conflicts_resolved_template,
            accessor='mrsrequest__conflicts_resolved__sum',
            verbose_name='Signalements resolus',
        )
    )

    search_fields = (
        'code',
        'name',
        'number',
    )

    filter_fields = (
        'active',
    )

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(
            models.Sum('mrsrequest__conflicts_accepted'),
            models.Sum('mrsrequest__conflicts_resolved'),
        )
        return qs

    @classmethod
    def reverse(cls, *args, **kwargs):
        return ''.join([
            str(super().reverse(*args, **kwargs)),
            '?active=2',
        ])


crudlfap.Router(
    Caisse,
    allowed_groups=['Admin'],
    material_icon='domain',
    views=[
        crudlfap.CreateView.clone(form_class=CaisseForm),
        crudlfap.DeleteView,
        crudlfap.UpdateView.clone(form_class=CaisseForm),
        crudlfap.DetailView,
        CaisseListView,
    ]
).register()


crudlfap.Router(
    Email,
    allowed_groups=['Admin'],
    material_icon='contact_mail',
    views=[
        crudlfap.ListView.clone(
            table_sequence=('email', 'caisse'),
        ),
    ]
).register()
