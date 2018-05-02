from crudlfap import crudlfap

from django import http
from django.contrib.staticfiles import finders
from django.views import generic

from mrsrequest.models import MRSRequest


class Dashboard(crudlfap.TemplateView):
    urlname = 'home'
    urlpath = ''
    title_heading = ''
    template_name = 'crudlfap/home.html'
    model = MRSRequest

    def get_queryset(self):
        return crudlfap.site[self.model].get_objects_for_user(
            self.request.user, [])

    def get_table(self):
        list_view = crudlfap.site['mrsrequest.MRSRequest'].views['list'].clone(
            request=self.request,
            object_list=self.queryset.status('inprogress'),
        )
        return list_view().table


class LegalView(generic.TemplateView):
    template_name = 'legal.html'


class FaqView(generic.TemplateView):
    template_name = 'faq.html'


class StatisticsView(generic.TemplateView):
    template_name = 'statistics.html'


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
            with open(path, 'r') as f:
                response = http.HttpResponse(
                    f.read(),
                    content_type=self.content_type,
                )

        if self.allow_origin:
            response['Access-Control-Allow-Origin'] = self.allow_origin

        return response
