from django import http
from django.views import generic

from mrsrequest.models import MRSRequest
from mrsrequest.views import MRSRequestCreateView

from .models import Institution


class InstitutionMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.institution = Institution.objects.filter(
            finess=kwargs['finess']
        ).first()

        if not self.institution:
            return http.HttpResponseNotFound()

        return super().dispatch(request, *args, **kwargs)


class InstitutionMRSRequestCreateView(InstitutionMixin, MRSRequestCreateView):
    base = 'base_iframe.html'

    def save(self):
        self.forms['mrsrequest'].instance.institution = self.institution
        return super().save()


class InstitutionMRSRequestIframeExampleView(generic.TemplateView):
    template_name = 'institution/mrsrequest_iframe_example.html'
    mrsrequest_statuses = MRSRequest.STATUS_CHOICES


class InstitutionMRSRequestStatusView(InstitutionMixin, generic.View):
    def get(self, request, *args, **kwargs):
        self.mrsrequest = self.institution.mrsrequest_set.filter(
            id=kwargs['mrsrequest_uuid']).first()

        if not self.mrsrequest:
            return http.HttpResponseNotFound()

        return http.JsonResponse(dict(
            status=self.mrsrequest.status,
        ))
