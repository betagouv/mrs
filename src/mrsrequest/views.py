import collections
import uuid

from django import http
from django.views import generic

from person.forms import InsuredForm, TransportedForm
from pmt.forms import PMTForm
from transport.forms import TransportForm

from .forms import CertifyForm
from .models import MRSRequest


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

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            self.mrsrequest_uuid = request.POST['mrsrequest_uuid']
            if not MRSRequest(id=self.mrsrequest_uuid).is_allowed(request):
                return http.HttpResponseBadRequest()
        else:
            self.mrsrequest_uuid = str(uuid.uuid4())
            MRSRequest(id=self.mrsrequest_uuid).allow(request)
        request.mrsrequest_uuid = self.mrsrequest_uuid

        self.forms = self.forms_factory()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        for form in self.forms:
            if not form.is_valid():
                return self.get(request, *args, **kwargs)

        return super().get(request, *args, **kwargs)
