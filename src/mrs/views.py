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

    def get_queryset(self):
        return crudlfap.site[MRSRequest].get_objects_for_user(
            self.request.user, [])

    def get_count_new(self):
        return self.queryset.filter(status=0).count()

    def get_count_valid(self):
        return self.queryset.filter(status=1).count()

    def get_count_invalid(self):
        return self.queryset.filter(status=2).count()

    def get_count_total(self):
        return self.queryset.count()


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

    def get(self, request, *args, **kwargs):
        path = finders.find(self.path)

        response = http.FileResponse(
            open(path, 'rb'),
            content_type=self.content_type,
        )

        if self.allow_origin:
            response['Access-Control-Allow-Origin'] = self.allow_origin

        return response
