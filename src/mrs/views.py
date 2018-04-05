from django import http
from django.contrib.staticfiles import finders
from django.views import generic


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
