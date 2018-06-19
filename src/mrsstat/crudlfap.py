import datetime
import json

from crudlfap import crudlfap

from django import forms

import django_filters

import material

from .models import Stat


class StatListView(crudlfap.ListView):
    keys = [
        'date',
        'mrsrequest_count_total',
        'mrsrequest_count_new',
        'mrsrequest_count_validated',
        'mrsrequest_count_rejected',
        'insured_shift_count',
    ]

    filter_fields = [
        'caisse',
        'institution',
    ]

    filterset_form_layout = material.Row(
        'caisse',
        'institution',
        'date__gt',
        'date__lt',
    )

    filterset_extra_class_attributes = dict(
        date__gt=django_filters.DateFilter(
            name='date',
            lookup_expr='gte',
            input_formats=['%d/%m/%Y'],
            widget=forms.TextInput(
                attrs={
                    'class': 'crudlfap-datepicker',
                    'data-clearable': 'true',
                    'data-format': 'dd/mm/yyyy',
                },
            )
        ),
        date__lt=django_filters.DateFilter(
            name='date',
            lookup_expr='lte',
            input_formats=['%d/%m/%Y'],
            widget=forms.TextInput(
                attrs={
                    'class': 'crudlfap-datepicker',
                    'data-clearable': 'true',
                    'data-format': 'dd/mm/yyyy',
                },
            ),
        ),
    )

    body_class = 'full-width'

    def get_filterset_data_default(self):
        today = datetime.date.today()
        return dict(
            date__gt=datetime.date(
                day=1,
                month=today.month,
                year=today.year,
            ).strftime('%d/%m/%Y'),
            date__lt=(
                datetime.date(
                    day=1,
                    month=today.month + 1 if today.month < 12 else 1,
                    year=today.year if today.month < 12 else today.year + 1,
                ) - datetime.timedelta(days=1)
            ).strftime('%d/%m/%Y'),
        )

    def get_object_list(self):
        qs = super().get_object_list()
        if not self.request.GET.get('caisse'):
            qs = qs.filter(caisse=None)
        if not self.request.GET.get('institution'):
            qs = qs.filter(institution=None)
        return qs

    def get_last_object(self):
        self.last_object = self.get_object_list().last()
        return self.last_object

    def get_chart_json(self):
        columns = [
            [
                'x'
                if k == 'date'
                else self.model._meta.get_field(k).verbose_name
            ]
            for k in self.keys
        ]

        rows = self.object_list.values_list(*self.keys)
        for row in rows:
            for i, value in enumerate(row):
                if isinstance(value, datetime.date):
                    columns[i].append(value.strftime('%Y-%m-%d'))
                else:
                    columns[i].append(value)

        return json.dumps(dict(
            bindto='#chart',
            data=dict(
                x='x',
                columns=columns,
            ),
            axis=dict(
                x=dict(
                    type='timeseries',
                    tick=dict(
                        format='%d/%m/%Y',
                    )
                )
            ),
            point=dict(
                show=False,
            )
        ))


crudlfap.Router(
    Stat,
    material_icon='multiline_chart',
    views=[
        StatListView(),
    ]
).register()
