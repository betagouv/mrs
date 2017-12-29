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


def form_errors(forms):
    return [form for form in forms.values() if not form.is_valid()]


class MRSRequestCreateView(generic.TemplateView):
    template_name = 'mrsrequest/form.html'

    def get(self, request, *args, **kwargs):
        self.object = MRSRequest()
        self.object.allow(request)
        self.mrsrequest_uuid = str(self.object.id)

        self.forms = collections.OrderedDict([
            ('pmt', PMTForm.factory(self)),
            ('person', PersonForm.factory(self)),
            ('transport', TransportForm.factory(self)),
            ('certify', CertifyForm()),
        ])

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not self.has_perm():
            return http.HttpResponseBadRequest()

        self.object = self.get_object()
        self.pmt = self.pmt_get_object()
        pmtform_data = MultiValueDict()
        if self.pmt:
            pmtform_data['pmtform-pmt'] = [self.pmt]
        self.bills = self.bills_get_queryset()
        transport_data = MultiValueDict(request.POST)
        if self.bills:
            transport_data['transportform-bills'] = self.bills

        self.forms = collections.OrderedDict([
            ('pmt', PMTForm.factory(
                self, data=pmtform_data, files=pmtform_data)),
            ('person', PersonForm.factory(self, data=request.POST)),
            ('transport', TransportForm.factory(
                self, data=transport_data, files=transport_data)),
            ('certify', CertifyForm(self.request.POST)),
        ])

        self.success = not form_errors(self.forms) and self.save()

        return generic.TemplateView.get(self, request, *args, **kwargs)

    def has_perm(self):
        if 'mrsrequest_uuid' not in self.request.POST:
            return False

        self.mrsrequest_uuid = self.request.POST['mrsrequest_uuid']

        # Let's not even load the object from db if request aint allowed
        if not MRSRequest(id=self.mrsrequest_uuid).is_allowed(self.request):
            return False

        return True

    def get_object(self):
        return MRSRequest.objects.filter(
            id=self.mrsrequest_uuid
        ).first() or MRSRequest(self.mrsrequest_uuid)

    def pmt_get_object(self):
        return PMT.objects.recorded_uploads(
            self.mrsrequest_uuid
        ).last()

    def bills_get_queryset(self):
        return Bill.objects.recorded_uploads(self.mrsrequest_uuid)

    def save(self):
        if not self.object.insured:
            # Update relation with existing Person
            self.object.insured = Person.objects.filter(
                birth_date=self.forms['person'].cleaned_data['birth_date'],
                nir=self.forms['person'].cleaned_data['nir'],
            ).first()

        if not self.object.insured:
            # Otherwise create a new Person
            self.object.insured = self.forms['person'].save()

        self.object.save()

        # Get form_id from insert trigger
        self.object.refresh_from_db()

        self.pmt.mrsrequest = self.object
        self.pmt.save()

        transport = self.forms['transport'].save(commit=False)
        transport.mrsrequest = self.object
        transport.save()

        self.bills.update(transport=transport)

        send_mail(
            template.loader.get_template(
                'mrsrequest/success_mail_title.txt'
            ).render(dict(view=self)).strip(),
            template.loader.get_template(
                'mrsrequest/success_mail_body.txt'
            ).render().strip(),
            settings.DEFAULT_FROM_EMAIL,
            [self.object.insured.email],
        )

        return True


class MRSRequestUpdateView(generic.TemplateView):
    mrsrequest_uuid = None
    template_name = 'admin/mrsrequest/change_form.html'

    def has_perm(self):
        return self.request.user.is_staff

    def get_object(self):
        if self.mrsrequest_uuid and self.request.user.is_staff:
            return MRSRequest.objects.get(id=self.mrsrequest_uuid)
        raise Exception('Must auth as staff to choose mrsrequest_uuid')

    def get(self, request, *args, **kwargs):
        if not self.has_perm():
            return http.HttpResponseBadRequest()

        self.object = self.get_object()
        self.object.allow(request)

        pmtform_initial = dict()
        try:
            self.object.pmt
        except PMT.DoesNotExist:
            pass
        else:
            pmtform_initial['pmt'] = [self.object.pmt]

        transport = self.object.transport_set.last()
        self.forms = collections.OrderedDict([
            ('pmt', PMTForm.factory(
                self,
                initial=pmtform_initial,
            )),
            ('person', PersonForm.factory(
                self, instance=self.object.insured)),
            ('transport', TransportForm.factory(
                self,
                instance=transport,
                initial=dict(bills=transport.bill_set.all())
            )),
        ])

        return generic.TemplateView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        pmtfiles = MultiValueDict()
        try:
            self.pmt = self.object.pmt
        except PMT.DoesNotExist:
            self.pmt = self.pmt_get_object()

        if self.pmt:
            pmtfiles['pmtform-pmt'] = [self.pmt]

        self.transport = self.object.transport_set.first()
        self.bills = self.bills_get_queryset()

        self.forms = collections.OrderedDict([
            ('pmt', PMTForm.factory(self, files=pmtfiles)),
            ('person', PersonForm.factory(
                self, instance=self.object.insured, data=request.POST)),
            ('transport', TransportForm.factory(
                self,
                instance=self.transport,
                files=MultiValueDict({'transportform-bills': [self.bills]}),
                data=request.POST,
            )),
        ])

        self.success = not form_errors(self.forms) and self.save()

        return generic.TemplateView.get(self, request, *args, **kwargs)

    def pmt_get_object(self):
        return PMT.objects.recorded_uploads(
            self.mrsrequest_uuid
        ).last()

    def bills_get_queryset(self):
        return Bill.objects.recorded_uploads(self.mrsrequest_uuid)

    def save(self):
        self.pmt.mrsrequest = self.object
        self.pmt.save()
        self.bills.update(transport=self.transport)
        self.forms['person'].save()
        self.forms['transport'].save()
        return True
