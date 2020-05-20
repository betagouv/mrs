from crudlfap import shortcuts as crudlfap

from django import http
from django.db import models
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import generic

from mrsrequest.models import MRSRequest
from person.models import Person


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
        )


class LegalView(generic.TemplateView):
    template_name = 'legal.html'


class FaqView(generic.TemplateView):
    template_name = 'faq.html'


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
        return http.HttpResponse(
            status=self.status,
            content=render_to_string(
                context=dict(
                    status=self.status,
                    message=self.message,
                ),
                template_name='error.html'
            )
        )


bad_request_view = ErrorView(400, 'Requête inacceptable (mauvais hostname?)')
forbidden_view = ErrorView(403, 'Page interdite')
not_found_view = ErrorView(404, 'Page introuvable')
internal_server_error_view = ErrorView(500, 'Erreur interne')


class MaintenanceView(generic.TemplateView):
    template_name = '503.html'
