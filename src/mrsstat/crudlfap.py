import datetime
import json

from crudlfap import crudlfap

from django import forms
from django.db import models

import django_filters

import material

from person.models import Person

from .models import Stat


class StatListView(crudlfap.ListView):
    material_icon = 'insert_chart'
    title_menu = 'quotidiennes'
    title_link = 'Graphique de statistiques quotidiennes'

    keys = [
        'date',
        'mrsrequest_count_new',
        'mrsrequest_count_inprogress',
        'mrsrequest_count_validated',
        'mrsrequest_count_rejected',
        'insured_shifts',
    ]

    date_args = [
        'date__gte',
        'date__lte',
    ]

    filter_fields = [
        'caisse',
        'institution',
    ]

    filterset_form_layout = material.Row(
        'caisse',
        'institution',
        *date_args
    )

    filterset_extra_class_attributes = dict(
        date__gte=django_filters.DateFilter(
            field_name='date',
            lookup_expr='gte',
            input_formats=['%d/%m/%Y'],
            label='Date minimale',
            widget=forms.TextInput(
                attrs={
                    'class': 'crudlfap-datepicker',
                    'data-clearable': 'true',
                    'data-format': 'dd/mm/yyyy',
                },
            )
        ),
        date__lte=django_filters.DateFilter(
            field_name='date',
            lookup_expr='lte',
            input_formats=['%d/%m/%Y'],
            label='Date maximale',
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

    def get_validation_average_delay(self):
        return self.object_list.aggregate(
            result=models.Avg('validation_average_delay')
        )['result']

    def get_mrsrequest_count(self, arg):
        return self.object_list.aggregate(
            result=models.Sum('mrsrequest_count_' + arg)
        )['result']

    def get_mrsrequests_by_shifted_insured_count(self):
        return self.mrsrequests.filter(insured__shifted=True).count()

    def get_savings(self):
        return self.object_list.aggregate(
            result=models.Sum('savings')
        )['result']

    def get_insured_shifts(self):
        return self.object_list.aggregate(
            result=models.Sum('insured_shifts')
        )['result']

    def get_insured_count_replied(self):
        kwargs = {i: self.date_values[i] for i in self.date_args}
        mrsrequests = self.mrsrequests.status_filter(
            'validated',
            'rejected',
            **kwargs
        )
        return Person.objects.filter(
            mrsrequest__in=mrsrequests
        ).distinct().count()

    def get_mrsrequests(self):
        # get our requests from the mrsrequest controller
        # because we are bichons <3
        controller = crudlfap.site['mrsrequest.MRSRequest']
        self.mrsrequests = controller.get_objects_for_user(self.request.user)
        for i in ('caisse', 'institution'):
            if self.filterset_form_cleaned_data.get(i, None):
                self.mrsrequests = self.mrsrequests.filter(**{
                    i: self.filterset_form_cleaned_data[i]
                })
        return self.mrsrequests

    def get_object_list(self):
        qs = super().get_object_list()
        self.object_list = self.filter_caisse_institution(qs)
        return self.object_list

    def get_filterset_form_cleaned_data(self):
        form = self.filterset.form
        if form.is_valid():
            self.filterset_form_cleaned_data = form.cleaned_data
        else:
            self.filterset_form_cleaned_data = self.filterset_data_default

    def get_filterset_data_default(self):
        today = datetime.date.today()
        return dict(
            date__gte=datetime.date(
                day=1,
                month=today.month,
                year=today.year,
            ).strftime('%d/%m/%Y'),
            date__lte=(
                datetime.date(
                    day=1,
                    month=today.month + 1 if today.month < 12 else 1,
                    year=today.year if today.month < 12 else today.year + 1,
                ) - datetime.timedelta(days=1)
            ).strftime('%d/%m/%Y'),
        )

    def get_date_values(self):
        today = datetime.date.today()
        gte = datetime.date(
            day=1,
            month=today.month,
            year=today.year,
        )
        lte = datetime.date(
            day=1,
            month=today.month + 1 if today.month < 12 else 1,
            year=today.year if today.month < 12 else today.year + 1,
        ) - datetime.timedelta(days=1)

        res = dict(date__gte=gte, date__lte=lte)
        if self.filterset.form.is_valid():
            if hasattr(self.filterset.form, 'cleaned_data'):
                for i in ('date__gte', 'date__lte'):
                    if i in self.filterset.form.cleaned_data:
                        res[i] = self.filterset.form.cleaned_data[i]
        self.date_values = res
        return res

    def filter_caisse_institution(self, qs):
        if not self.request.GET.get('caisse'):
            qs = qs.filter(caisse=None)
        if not self.request.GET.get('institution'):
            qs = qs.filter(institution=None)
        return qs

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
                ),
                y=dict(
                    min=0,
                    padding=dict(bottom=0),
                ),
            ),
            point=dict(
                show=len(rows) == 1,
            )
        ))


class StatListTotalsView(StatListView):
    urlname = 'total'
    urlpath = 'total'
    template_name = 'mrsstat/stat_list.html'
    material_icon = 'show_chart'
    title_menu = 'cumulatives'
    title_link = 'Graphique de statistiques cumulatives'

    keys = [
        'date',
        'mrsrequest_total_new',
        'mrsrequest_total_inprogress',
        'mrsrequest_total_validated',
        'mrsrequest_total_rejected',
        'insured_shifts_total',
    ]


class StatImportExport(crudlfap.ModelView):
    material_icon = 'compare_arrows'
    title_link = 'Importer et exporter des fichiers CSV'


class StatRouter(crudlfap.Router):
    model = Stat
    material_icon = 'multiline_chart'
    views = [
        StatImportExport,
        StatListView,
        StatListTotalsView,
    ]

    def allowed(self, view):
        profile = getattr(view.request.user, 'profile', None)
        if profile in ('admin', 'stat'):
            return True

StatRouter().register()
