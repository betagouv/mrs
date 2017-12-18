import collections

from material.frontend.views import ModelViewSet

from django import http
from django.views import generic

from person.forms import InsuredForm, TransportedForm
from pmt.forms import PMTForm
from transport.forms import TransportForm

from .forms import CertifyForm
from .models import MRSRequest


class MRSRequestViewSet(ModelViewSet):
    model = MRSRequest


class MRSRequestCreateView(generic.TemplateView):
    template_name = 'mrsrequest/form.html'
    form_classes = [
        PMTForm,
        TransportedForm,
        InsuredForm,
        TransportForm,
        CertifyForm
    ]

    def forms_factory(self):
        forms = collections.OrderedDict()
        for form_class in self.form_classes:
            forms[form_class.__name__] = form_class.factory(self)
        return forms

    def get_mrsrequest_uuid(self, request):
        if request.method == 'POST':
            if 'mrsrequest_uuid' not in request.POST:
                return False

            mrsrequest_uuid = request.POST['mrsrequest_uuid']
            if not MRSRequest(id=mrsrequest_uuid).is_allowed(request):
                return False
            return mrsrequest_uuid
        else:
            mrsrequest = MRSRequest()
            mrsrequest.allow(request)
            return str(mrsrequest.id)

    def dispatch(self, request, *args, **kwargs):
        request.mrsrequest_uuid = self.get_mrsrequest_uuid(request)
        if not request.mrsrequest_uuid:
            return http.HttpResponseBadRequest()
        self.forms = self.forms_factory()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        for form in self.forms:
            if not form.is_valid():
                return self.get(request, *args, **kwargs)

        return super().get(request, *args, **kwargs)
