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
        'conflicting',
        'conflicted',
        'resolved',
        'contacts',
        'import_datetime',
    )

    table_columns = dict(
        conflicting=tables.Column(
            accessor='conflicting',
            verbose_name='Signalements liquidateurs',
        ),
        conflicted=tables.Column(
            accessor='conflicted',
            verbose_name='Signalements assurés',
        ),
        resolved=tables.Column(
            accessor='resolved',
            verbose_name='Signalements traités',
        ),
        contacts=tables.TemplateColumn(
            '{{ record.contacts }}',
            accessor='contacts',
            verbose_name='Reclamations',
        ),
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
            conflicted=models.Sum('stat__mrsrequest_count_conflicted'),
            conflicting=models.Sum('stat__mrsrequest_count_conflicting'),
            resolved=models.Sum('stat__mrsrequest_count_resolved'),
            contacts=models.Count('contact', distinct=True),
        )
        return qs

    @classmethod
    def reverse(cls, *args, **kwargs):
        return ''.join([
            str(super().reverse(*args, **kwargs)),
            '?active=2',
        ])


class CaisseDetailView(crudlfap.DetailView):
    def get_contact_subjects_counts(self):
        choices = dict(self.object.contact_set.model.SUBJECT_CHOICES)
        qs = self.object.contact_set.values('subject').annotate(
            total=models.Count('subject')
        ).order_by('total')
        return {
            choices[res['subject']]: res['total']
            for res in qs
        }


crudlfap.Router(
    Caisse,
    allowed_groups=['Admin'],
    material_icon='domain',
    views=[
        crudlfap.CreateView.clone(form_class=CaisseForm),
        crudlfap.DeleteView,
        crudlfap.UpdateView.clone(form_class=CaisseForm),
        CaisseDetailView,
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
