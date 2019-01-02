from crudlfap import shortcuts as crudlfap

from django.db import models

import django_tables2 as tables

from .forms import CaisseForm
from .models import Caisse, Email


class CaisseListView(crudlfap.ListView):
    table_sequence = (
        'code',
        'name',
        'number',
        'active',
        'score',
        'confirms',
        'import_datetime',
    )

    table_columns = dict(
        confirms=tables.Column(
            accessor='mrsrequest__confirms__sum',
            verbose_name='Alertes',
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
            models.Sum('mrsrequest__confirms')
        )
        return qs

crudlfap.Router(
    Caisse,
    allowed_groups=['Admin'],
    material_icon='domain',
    views=[
        crudlfap.CreateView.clone(form_class=CaisseForm),
        crudlfap.DeleteView,
        crudlfap.UpdateView,
        crudlfap.DetailView.clone(form_class=CaisseForm),
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
