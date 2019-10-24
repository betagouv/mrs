import pytz
import traceback

from crudlfap import shortcuts as crudlfap

from django import forms
from django import http
from django.conf import settings
from django.contrib.staticfiles import finders
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from caisse.models import Caisse
from mrsrequest.models import MRSRequest
from person.models import Person
from raven import Client


class Dashboard(crudlfap.TemplateView):
    urlname = 'home'
    urlpath = ''
    title_heading = ''
    template_name = 'crudlfap/home.html'
    model = MRSRequest
    body_class = 'full-width'
    allowed_groups = [
        'Admin',
        'UPN',
        'Support',
        'Stat',
        'Superviseur',
        'Admin Local'
    ]
    material_icon = 'home'

    def get_listview(self):
        router = crudlfap.site['mrsrequest.MRSRequest']
        self.listview = router.views['list'].clone(
            request=self.request,
            object_list=self.queryset.in_status_by(
                'inprogress', self.request.user),
        )()
        return self.listview

    def get_listactions(self):
        return self.listview.listactions

    def get_table(self):
        return self.listview.table

    def get_queryset(self):
        return crudlfap.site[self.model].get_queryset(self)

    def get(self, *args, **kwargs):
        if self.request.user.profile == 'support':
            return http.HttpResponseRedirect(
                reverse('crudlfap:mrsrequest:list')
            )
        elif self.request.user.profile == 'admin local':
            return http.HttpResponseRedirect(
                reverse('crudlfap:user:list')
            )
        return super().get(*args, **kwargs)


class IndexView(generic.TemplateView):
    template_name = 'index.html'

    @property
    def users_count(self):
        return Person.objects.count()

    @property
    def mrsrequests_count(self):
        return MRSRequest.objects.count()

    @property
    def average_payment_delay(self):
        return '{:0.2f}'.format(
            MRSRequest.objects.aggregate(
                result=models.Avg('delay')
            )['result'] or 0
        ).replace('.', ',')


class LegalView(generic.TemplateView):
    template_name = 'legal.html'


class FaqView(generic.TemplateView):
    template_name = 'faq.html'


class StatisticsView(crudlfap.Factory, generic.TemplateView):
    template_name = 'statistics.html'

    class Form(forms.Form):
        caisse = forms.ModelChoiceField(
            Caisse.objects.filter(active=True),
        )

    def get_form(self):
        if self.request.GET.get('caisse', None):
            self.form = self.Form(self.request.GET)
        else:
            self.form = self.Form()

    def qs_form_filter(self, qs):
        if self.form.is_valid() and self.form.cleaned_data.get('caisse', None):
            return qs.filter(caisse=self.form.cleaned_data['caisse'])
        return qs

    def get_mrsrequests(self):
        return self.qs_form_filter(MRSRequest.objects.all())

    def get_mrsrequests_processed(self):
        return self.mrsrequests.processed().count() or 0

    def get_average_payment_delay(self):
        return '{:0.2f}'.format(
            self.mrsrequests.aggregate(
                result=models.Avg('delay')
            )['result'] or 0
        ).replace('.', ',')

    def get_insured_shifts(self):
        return self.mrsrequests.filter(insured__shifted=True).count()

    def get_shifted_insured_count(self):
        return Person.objects.filter(
            shifted=True,
            mrsrequest__in=self.mrsrequests,
        ).distinct().count()

    def get_insured_count(self):
        return Person.objects.filter(
            mrsrequest__in=self.mrsrequests
        ).distinct().count()

    def get_savings(self):
        return self.mrsrequests.aggregate(
            result=models.Sum('saving')
        )['result'] or 0

    def get_now(self):
        return timezone.now().astimezone(
            pytz.timezone(settings.TIME_ZONE)
        ).strftime('%d/%m/%Y %H:%M:%S')


class StaticView(generic.View):
    path = None
    content_type = None
    allow_origin = None
    stream = True

    def get(self, request, *args, **kwargs):
        path = finders.find(self.path)

        if self.stream:
            response = http.FileResponse(
                open(path, 'rb'),
                content_type=self.content_type,
            )
        else:
            with open(path, 'r', encoding='utf8') as f:
                response = http.HttpResponse(
                    f.read(),
                    content_type=self.content_type,
                )

        if self.allow_origin:
            response['Access-Control-Allow-Origin'] = self.allow_origin

        return response


class ErrorView:

    def __init__(self, status, message):
        self.status = status
        self.message = message

    def __call__(self, request, *args, **kwargs):
        client = Client(settings.RAVEN_CONFIG['dsn'])
        traceback.print_exc()

        if isinstance(kwargs.get('exception', None), Exception):
            client.captureException(kwargs['exception'])
        elif self.status in (500, 400):
            client.captureMessage(self.message, level='error')

        return http.HttpResponse(
            status=self.status,
            content=render_to_string(
                context=dict(
                    status=self.status,
                    message=self.message,
                ),
                template_name=f'error.html'
            )
        )


bad_request_view = ErrorView(400, 'Requête inacceptable (mauvais hostname?)')
forbidden_view = ErrorView(403, 'Page interdite')
not_found_view = ErrorView(404, 'Page introuvable')
internal_server_error_view = ErrorView(500, 'Erreur interne')


class MaintenanceView(generic.TemplateView):
    template_name = '503.html'
