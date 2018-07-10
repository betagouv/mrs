from crudlfap import crudlfap

from django import forms
from django import http
from django.contrib.staticfiles import finders
from django.db import models
from django.utils import timezone
from django.views import generic

from caisse.models import Caisse
from mrsrequest.models import MRSRequest
from person.models import Person


class Dashboard(crudlfap.TemplateView):
    urlname = 'home'
    urlpath = ''
    title_heading = ''
    template_name = 'crudlfap/home.html'
    model = MRSRequest

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
        return crudlfap.site[self.model].get_objects_for_user(
            self.request.user, [])


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

    def get_insured_count(self):
        return Person.objects.filter(
            mrsrequest__in=self.mrsrequests
        ).distinct().count()

    def get_savings(self):
        return self.mrsrequests.aggregate(
            result=models.Sum('saving')
        )['result'] or 0

    def get_now(self):
        return timezone.now().strftime('%d/%m/%Y %H:%M:%S')


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
