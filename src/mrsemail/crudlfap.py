import json

from crudlfap import shortcuts as crudlfap
from django import template
from django import forms
from django.conf import settings
from django.db import models

from caisse.models import Caisse
from djcall.models import Caller
import django_tables2 as tables
import django_filters

from mrs.settings import DATE_FORMAT_FR

from .forms import EmailForm
from .models import EmailTemplate


class EmailViewMixin:
    template_name = 'mrsemail/form.html'
    body_class = 'modal-fixed-footer'
    form_class = EmailForm

    def log_insert(self):
        if hasattr(self, 'object_list'):
            objects = self.object_list
        else:
            objects = [self.object]

        for obj in objects:
            obj.logentries.create(
                user=self.request.user,
                comment=self.log_message,
                data=self.log_data,
                action=self.action_flag,
            )

    def get_log_data(self):
        return dict(
            body=self.form.cleaned_data['body'],
            subject=self.form.cleaned_data['subject'],
        )

    def get_log_message(self):
        return self.form.cleaned_data['template']

    def get_form(self):
        form = super().get_form() or self.form
        qs = form.fields['template'].queryset
        form.fields['template'].queryset = qs.filter(
            menu=self.emailtemplates_menu
        )
        return form

    def templates_json(self):
        context = template.Context({'display_id': self.object.display_id})
        templates = {
            i.pk: dict(
                subject=template.Template(i.subject).render(context),
                body=template.Template(i.body).render(context),
            ) for i in EmailTemplate.objects.filter(
                menu=self.emailtemplates_menu
            )
        }
        return json.dumps(templates)

    def form_valid(self):
        Caller(
            callback='djcall.django.email_send',
            kwargs=dict(
                subject=self.form.cleaned_data['subject'],
                body=self.form.cleaned_data['body'],
                to=[self.object.insured.email],
                reply_to=[settings.TEAM_EMAIL],
            )
        ).spool('mail')
        self.form.cleaned_data['template'].counter += 1
        self.form.cleaned_data['template'].save()
        return super().form_valid()


class CaissesFilter(django_filters.ModelMultipleChoiceFilter):
    def filter(self, qs, value):
        return qs


class DateFilter(django_filters.DateFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('input_formats', [DATE_FORMAT_FR])
        kwargs.setdefault('widget', forms.TextInput(
            attrs={
                'class': 'crudlfap-datepicker',
                'data-clearable': 'true',
                'data-format': 'dd/mm/yyyy',
            },
        ))
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        return qs


class EmailTemplateListView(crudlfap.ListView):
    table_columns = dict(
        new_counter=tables.Column(
            accessor='new_counter',
            verbose_name='Nouveau compte',
        ),
    )
    search_fields = [
        'name',
        'subject',
        'body',
    ]

    filterset_extra_class_attributes = dict(
        caisse=CaissesFilter(queryset=Caisse.objects.all()),
        datemin=DateFilter(lookup_expr='gte', label='Date minimale'),
        datemax=DateFilter(lookup_expr='lte', label='Date maximale'),
    )

    def get_filterset(self):
        filterset = super().get_filterset() or self.filterset
        form = filterset.form
        if 'caisse' in form.fields and self.request.user.profile != 'admin':
            form.fields['caisse'].queryset = self.request.user.caisses.all()
        return filterset

    def get_show_caisse_filter(self):
        self.show_caisse_filter = (
            self.request.user.caisses.count() > 1
            or self.request.user.profile == 'admin'
        )

    def get_filter_fields(self):
        filter_fields = []
        if self.show_caisse_filter:
            filter_fields.append('caisse')
        return filter_fields

    def get_object_list(self):
        qs = self.search_form.get_queryset()

        filtr = models.Q()
        if self.filterset.form.is_valid():
            caisses = self.filterset.form.cleaned_data.get('caisse', None)
            datemin = self.filterset.form.cleaned_data.get('datemin', None)
            datemax = self.filterset.form.cleaned_data.get('datemax', None)

            if caisses:
                filtr = filtr & models.Q(
                    mrsrequestlogentry__mrsrequest__caisse__in=caisses
                )

        qs = qs.annotate(
            new_counter=models.Count(
                'mrsrequestlogentry',
                distinct=True,
                filter=filtr
            ),
        )

        return qs

        return super().get_object_list()
        if value:
            qs = qs.annotate(
                new_counter=models.Count(
                    'mrsrequestlogentry',
                    distinct=True,
                    filter=models.Q(mrsrequestlogentry__mrsrequest__caisse__in=value)
                ),
            )
        else:
            qs = qs.annotate(
                new_counter=models.Count(
                    'mrsrequestlogentry',
                    distinct=True,
                ),
            )


crudlfap.Router(
    EmailTemplate,
    allowed_groups=['Admin'],
    material_icon='mail',
    views=[
        EmailTemplateListView,
        crudlfap.CreateView,
        crudlfap.UpdateView,
    ]
).register()
