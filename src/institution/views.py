import uuid

from django import http
from django.contrib.staticfiles import finders
from django.urls import reverse
from django.views import generic

from mrsrequest.models import MRSRequest
from mrsrequest.views import MRSRequestCreateView

from .models import Institution


class ExampleJpg(generic.View):
    def get(self, request, *args, **kwargs):
        path = finders.find(
            'img/mrsHeaderFiltreBleu-logo_ito86r.jpg',
        )

        response = http.FileResponse(
            open(path, 'rb'),
            content_type='image/jpeg',
        )

        response['Access-Control-Allow-Origin'] = '*'
        return response


class InstitutionMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.institution = Institution.objects.filter(
            finess=kwargs['finess']
        ).first()

        if not self.institution:
            return http.HttpResponseNotFound()

        response = super().dispatch(request, *args, **kwargs)

        if self.institution.dynamic_allow:
            if 'origin' not in request.GET:
                return http.HttpResponseBadRequest('"origin" required in GET')

            response['X-Frame-Options'] = 'ALLOW-FROM {}'.format(
                request.GET['origin']
            )
            response['Access-Control-Allow-Origin'] = '*'
            self.ALLOW_INSECURE = True
        else:
            response['X-Frame-Options'] = 'ALLOW-FROM {}'.format(
                self.institution.origin)
            response['Access-Control-Allow-Origin'] = self.allow_origin()

        return response

    def allow_origin(self):
        return '/'.join(self.institution.origin.split('/')[:3])


class InstitutionMRSRequestCreateView(InstitutionMixin, MRSRequestCreateView):
    base = 'base_iframe.html'

    def save(self):
        self.forms['mrsrequest'].instance.institution = self.institution
        return super().save()


class InstitutionMRSRequestIframeExampleView(generic.TemplateView):
    template_name = 'institution/mrsrequest_iframe_example.html'
    mrsrequest_statuses = MRSRequest.STATUS_CHOICES

    def iframe_url(self):
        if 'iframeurl' in self.request.GET:
            url = self.request.GET['iframeurl']
        else:
            url = self.base_url() + reverse(
                'institution:mrsrequest_iframe',
                args=[self.kwargs['finess']]
            )
        return url

    def iframe_base_url(self):
        return '/'.join(self.iframe_url().split('/')[:3])

    def base_url(self):
        return '/'.join(self.request.build_absolute_uri().split('/')[:3])

    def pmt_url(self):
        """Return example url to a PMT file"""
        if 'pmturl' in self.request.GET:
            return self.request.GET['pmturl']
        else:
            return self.base_url() + reverse('institution:example_jpg')


class InstitutionMRSRequestStatusView(InstitutionMixin, generic.View):
    def get(self, request, *args, **kwargs):
        try:
            uuid.UUID(kwargs['mrsrequest_uuid'])
        except ValueError:
            return http.HttpResponseBadRequest('Malformed UUID')

        self.mrsrequest = self.institution.mrsrequest_set.filter(
            id=kwargs['mrsrequest_uuid']).first()

        if not self.mrsrequest:
            return http.HttpResponseNotFound('MRSRequest not found')

        return http.JsonResponse(dict(
            status=self.mrsrequest.status,
        ))
