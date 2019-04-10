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
from mrsrequest.models import datetime_max, datetime_min
from mrsuser.models import User

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
                emailtemplate=self.form.cleaned_data['template'],
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


class NoopFilter:
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
    allowed_groups = ['Admin', 'UPN', 'Superviseur']
    table_columns = dict(
        new_counter=tables.Column(
            accessor='new_counter',
            verbose_name='Utilisations',
        ),
    )
    search_fields = [
        'name',
        'subject',
        'body',
    ]

    def get_caisses(self):
        if self.request.user.profile == 'admin':
            return Caisse.objects.all()
        return self.request.user.caisses.all()

    def get_show_caisse_filter(self):
        self.show_caisse_filter = (
            self.request.user.caisses.count() > 1
            or self.request.user.profile == 'admin'
        )

    def get_show_user_filter(self):
        self.show_user_filter = self.request.user.profile != 'upn'

    def get_filterset_extra_class_attributes(self):
        ret = dict(
            datemin=DateFilter(lookup_expr='gte', label='Date minimale'),
            datemax=DateFilter(lookup_expr='lte', label='Date maximale'),
            menu=django_filters.ChoiceFilter(
                choices=EmailTemplate.MENU_CHOICES
            )
        )

        if self.show_caisse_filter:
            ret['caisse'] = type(
                'CaissesFilter',
                (NoopFilter, django_filters.ModelMultipleChoiceFilter),
                dict()
            )(
                label='Caisses',
                queryset=self.caisses
            )

        if self.show_user_filter:
            qs = User.objects.all()
            if self.request.user.profile != 'admin':
                qs = qs.filter(caisses__in=self.caisses)

            ret['user'] = type(
                'UserFilter',
                (NoopFilter, django_filters.ModelChoiceFilter),
                dict()
            )(
                label='Utilisateur',
                queryset=qs
            )

        return ret

    def get_object_list(self):
        self.object_list = super().get_object_list()

        filtr = models.Q()
        if self.filterset.form.is_valid():
            caisses = self.filterset.form.cleaned_data.get('caisse', None)
            datemin = self.filterset.form.cleaned_data.get('datemin', None)
            datemax = self.filterset.form.cleaned_data.get('datemax', None)
            user = self.filterset.form.cleaned_data.get('user', None)

            if caisses:
                filtr = filtr & models.Q(
                    mrsrequestlogentry__mrsrequest__caisse__in=caisses
                )

            if datemin:
                filtr = filtr & models.Q(
                    mrsrequestlogentry__datetime__gte=datetime_min(datemin)
                )

            if datemax:
                filtr = filtr & models.Q(
                    mrsrequestlogentry__datetime__lte=datetime_max(datemax)
                )

            if user:
                filtr = filtr & models.Q(mrsrequestlogentry__user=user)

        if self.request.user.profile == 'upn':
            filtr = filtr & models.Q(
                mrsrequestlogentry__user=self.request.user
            )

        self.object_list = self.object_list.annotate(
            new_counter=models.Count(
                'mrsrequestlogentry',
                distinct=True,
                filter=filtr
            ),
        )

        return self.object_list


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
