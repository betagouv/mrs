import datetime
import urllib.parse

from crudlfap import shortcuts as crudlfap

from django import forms
from django.db import models

import django_filters

import material
from django.db.models import Count

from mrsrequest.models import MRSRequest
from person.models import Person

from .models import Stat


class StatListView(crudlfap.ListView):
    material_icon = 'show_chart'
    title_menu = 'suivi des indicateurs'
    title_link = 'Suivi des indicateurs'

    date_args = [
        'date__gte',
        'date__lte',
    ]

    filter_fields = [
        'caisse',
    ]

    filterset_form_layout = material.Row(
        'caisse',
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

    def get_filterset(self):
        filterset = super().get_filterset() or self.filterset
        form = filterset.form
        if 'caisse' in form.fields and self.request.user.profile != 'admin':
            form.fields['caisse'].queryset = self.request.user.caisses.all()
        return filterset

    body_class = 'full-width'

    @classmethod
    def reverse(cls, *args, **kwargs):
        params = {
            str(k): str(v)
            for k, v in cls.date_default_filters.items()
        }

        if cls.request.user.profile != 'admin':
            params['caisse'] = cls.request.user.caisses.first().pk

        return ''.join([
            str(super().reverse(*args, **kwargs)),
            '?',
            # pure abuse of Factory below
            urllib.parse.urlencode(params)
        ])

    def get_date_default_filters(self):
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

    def get_insured_shifts(self):
        return self.object_list.aggregate(
            result=models.Sum('insured_shifts')
        )['result']

    def get_insured_count_replied(self):
        mrsrequests = self.mrsrequests.status_filter(
            'validated',
            'rejected',
            **{
                k: v
                for k, v in self.filterset.form.cleaned_data.items()
                if k.startswith('date_')
            }
        )
        return Person.objects.filter(
            mrsrequest__in=mrsrequests
        ).distinct().count()

    def get_insured_count(self):
        mrsrequests = self.mrsrequests.created(
            **{
                k: v
                for k, v in self.filterset.form.cleaned_data.items()
                if k.startswith('date_')
            },
            caisse=self.filterset.form.cleaned_data.get('caisse')
        )
        return Person.objects.filter(
            mrsrequest__in=mrsrequests
        ).distinct().count()

    def get_shifted_insured_count(self):
        caisse_set = self.filterset.form.cleaned_data.get('caisse')
        if caisse_set:
            mrsrequests = self.mrsrequests.filter(
                caisse=caisse_set
            )
        else:
            mrsrequests = self.mrsrequests
        return Person.objects.filter(
            shifted=True,
            mrsrequest__in=mrsrequests
        ).distinct().count()

    def get_mrsrequests_processed(self):
        mrsrequests = self.mrsrequests.created(
            **{
                k: v
                for k, v in self.filterset.form.cleaned_data.items()
                if k.startswith('date_')
            },
            caisse=self.filterset.form.cleaned_data.get('caisse')
        ).filter(
            status__in=(
                MRSRequest.STATUS_VALIDATED,
                MRSRequest.STATUS_REJECTED,
            ),
        )
        return mrsrequests.distinct().count()

    def get_average_payment_delay(self):
        mrsrequests = self.mrsrequests.created(
            **{
                k: v
                for k, v in self.filterset.form.cleaned_data.items()
                if k.startswith('date_')
            },
            caisse=self.filterset.form.cleaned_data.get('caisse')
        )
        return '{:0.2f}'.format(
            mrsrequests.aggregate(
                result=models.Avg('delay')
            )['result'] or 0
        ).replace('.', ',')

    def get_savings(self):
        mrsrequests = self.mrsrequests.created(
            **{
                k: v
                for k, v in self.filterset.form.cleaned_data.items()
                if k.startswith('date_')
            },
            caisse=self.filterset.form.cleaned_data.get('caisse')
        )
        return mrsrequests.aggregate(
            result=models.Sum('saving')
        )['result']

    def get_primo_users(self):
        mrsrequests = self.mrsrequests.created(
            **{
                k: v
                for k, v in self.filterset.form.cleaned_data.items()
                if k.startswith('date_')
            },
            caisse=self.filterset.form.cleaned_data.get('caisse')
        )
        return Person.objects.annotate(
            requestscount=Count('mrsrequest')
        ).filter(
            requestscount=1,
            mrsrequest__in=mrsrequests
        ).distinct().count()

    def get_mrsrequests(self):
        # the default controller's list view will return objects user can see
        controller = crudlfap.site['mrsrequest.MRSRequest']
        self.mrsrequests = controller['list'](
            request=self.request
        ).get_objects()
        for i in ('caisse'):
            if self.filterset.form.cleaned_data.get(i, None):
                self.mrsrequests = self.mrsrequests.filter(**{
                    i: self.filterset_form_cleaned_data[i]
                })
        return self.mrsrequests

    def get_object_list(self):
        qs = super().get_object_list()
        self.object_list = self.filter_caisse(qs)
        return self.object_list

    def filter_caisse(self, qs):
        if not self.request.GET.get('caisse'):
            qs = qs.filter(caisse=None)
        return qs


class StatImportExport(crudlfap.ModelView):
    material_icon = 'compare_arrows'
    title_link = 'Importer et exporter des fichiers CSV'
    allowed_groups = ['Admin', 'Stat']


class StatRouter(crudlfap.Router):
    allowed_groups = ['Admin', 'Stat', 'Superviseur']
    model = Stat
    material_icon = 'multiline_chart'
    views = [
        StatImportExport,
        StatListView,
    ]

    def get_queryset(self, view):
        user = view.request.user

        if user.is_superuser or user.profile == 'admin':
            return self.model.objects.all()
        elif user.profile in ('stat', 'superviseur'):
            return self.model.objects.filter(
                caisse__in=view.request.user.caisses.all()
            )

        return self.model.objects.none()

StatRouter().register()
