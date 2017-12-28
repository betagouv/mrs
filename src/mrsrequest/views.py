import collections

from django import http
from django import template
from django.conf import settings
from django.core.mail import send_mail
from django.utils.datastructures import MultiValueDict
from django.views import generic

from person.forms import PersonForm
from person.models import Person
from pmt.models import PMT
from pmt.forms import PMTForm
from transport.models import Bill
from transport.forms import TransportForm

from .forms import CertifyForm
from .models import MRSRequest


class MRSRequestCreateView(generic.TemplateView):
    template_name = 'mrsrequest/form.html'

    def __init__(self, *a, **k):
        self.forms = collections.OrderedDict()
        super().__init__(*a, **k)

    def get(self, request, *args, **kwargs):
        self.object = MRSRequest()
        self.object.allow(request)
        self.mrsrequest_uuid = str(self.object.id)

        self.forms = collections.OrderedDict()
        self.forms['pmt'] = PMTForm.factory(self)
        self.forms['person'] = PersonForm.factory(self)
        self.forms['transport'] = TransportForm.factory(self)
        self.forms['certify'] = CertifyForm()

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not self.has_perm():
            return http.HttpResponseBadRequest()

        self.data = MultiValueDict(request.POST)
        self.hydrate()

        for form in self.forms.values():
            form.is_valid()
        errors = [form for form in self.forms.values() if not form.is_valid()]
        if not errors:
            if self.save():
                self.success = True
                return self.get(request, *args, **kwargs)

        return generic.TemplateView.get(self, request, *args, **kwargs)

    def has_perm(self):
        if 'mrsrequest_uuid' not in self.request.POST:
            return False

        self.mrsrequest_uuid = self.request.POST['mrsrequest_uuid']

        # Let's not even load the object from db if request aint allowed
        if not MRSRequest(id=self.mrsrequest_uuid).is_allowed(self.request):
            return False

        return True

    def hydrate(self):
        self.object = MRSRequest.objects.filter(
            id=self.mrsrequest_uuid
        ).first() or MRSRequest(self.mrsrequest_uuid)

        self.hydrate_pmt()
        self.hydrate_person()
        self.hydrate_transport()
        self.forms['certify'] = CertifyForm(self.data)

    def hydrate_person(self):
        birth_date = self.data.get('birth_date', None)
        nir = self.data.get('nir', None)

        self.person = None
        if nir and birth_date:
            self.person = Person.objects.filter(
                birth_date=birth_date,
                nir=nir,
            ).first()

        self.forms['person'] = PersonForm.factory(self, self.data)

    def hydrate_pmt(self):
        self.pmt = PMT.objects.recorded_uploads(
            self.mrsrequest_uuid
        ).last()

        if self.pmt and self.pmt.filename:
            self.data['pmtform-pmt'] = [self.pmt]
        else:
            self.data['pmtform-pmt'] = []

        self.forms['pmt'] = PMTForm.factory(self, self.data, files=self.data)

    def hydrate_transport(self):
        self.transport = (
            self.object.transport_set.first()
            if self.object else None
        )

        self.bills = Bill.objects.recorded_uploads(self.mrsrequest_uuid)

        if self.bills:
            self.data['transportform-bills'] = self.bills
        else:
            self.data['transportform-bills'] = []

        self.forms['transport'] = TransportForm.factory(
            self, self.data, files=self.data, instance=self.transport)

    def save(self):
        if not self.person:
            # Never trust input sources to update data !
            # Support create only.
            self.person = self.forms['person'].save()
        self.object.insured = self.person
        self.object.save()

        self.pmt.mrsrequest = self.object
        self.pmt.save()

        transport = self.forms['transport'].save(commit=False)
        transport.mrsrequest = self.object
        transport.save()

        self.bills.update(transport=transport)

        self.object.refresh_from_db()
        send_mail(
            template.loader.get_template(
                'mrsrequest/success_mail_title.txt'
            ).render(dict(view=self)).strip(),
            template.loader.get_template(
                'mrsrequest/success_mail_body.txt'
            ).render().strip(),
            settings.DEFAULT_FROM_EMAIL,
            [self.person.email],
        )

        return True
