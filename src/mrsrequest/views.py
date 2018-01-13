import collections

from django import http
from django import template
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.datastructures import MultiValueDict
from django.views import generic

from person.forms import PersonForm

from .forms import CertifyForm, MRSRequestForm
from .models import Bill, MRSRequest, PMT, Transport


class MRSRequestFormViewMixin(object):
    def form_errors(self):
        return [form for form in self.forms.values() if not form.is_valid()]

    def form_data(self):
        data = MultiValueDict(self.request.POST)
        if self.pmt:
            data['mrsrequestform-pmt'] = [self.pmt]
        if self.bills:
            data['mrsrequestform-bills'] = self.bills
        return data


class MRSRequestCreateView(MRSRequestFormViewMixin, generic.TemplateView):
    template_name = 'mrsrequest/form.html'

    def get(self, request, *args, **kwargs):
        self.object = MRSRequest()
        self.object.allow(request)
        self.mrsrequest_uuid = str(self.object.id)

        self.forms = collections.OrderedDict([
            ('mrsrequest', MRSRequestForm.factory(self)),
            ('person', PersonForm.factory(self)),
            ('certify', CertifyForm()),
        ])

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.mrsrequest_uuid = self.request.POST.get('mrsrequest_uuid', None)

        if not self.mrsrequest_uuid:  # require mrsrequest_uuid on post
            return http.HttpResponseBadRequest()

        # view is supposed to create a new request
        try:
            if MRSRequest.objects.filter(id=self.mrsrequest_uuid):
                return http.HttpResponseBadRequest()
        except ValidationError:  # badly formated uuid
            return http.HttpResponseBadRequest()

        # Let's not even load the object from db if request aint allowed
        if not MRSRequest(id=self.mrsrequest_uuid).is_allowed(self.request):
            return http.HttpResponseBadRequest()

        self.object = MRSRequest(id=self.mrsrequest_uuid)
        self.pmt = PMT.objects.recorded_uploads(self.mrsrequest_uuid).last()
        self.bills = Bill.objects.recorded_uploads(self.mrsrequest_uuid)

        data = self.form_data()

        self.forms = collections.OrderedDict([
            ('mrsrequest', MRSRequestForm.factory(
                self, data=data, files=data)),
            ('person', PersonForm.factory(self, data=request.POST)),
            ('certify', CertifyForm(self.request.POST)),
        ])

        with transaction.atomic():
            self.success = not self.form_errors() and self.save()

        return generic.TemplateView.get(self, request, *args, **kwargs)

    def save(self):
        # Update relation with existing Person
        self.object.insured = self.forms['person'].get_or_create()
        self.object.save()

        # Assign uploaded PMT
        self.pmt.mrsrequest = self.object
        self.pmt.save()

        # Assign uploaded Bills
        self.bills.update(mrsrequest=self.object)

        Transport.objects.create(
            mrsrequest=self.object,
            date_depart=self.forms['mrsrequest'].cleaned_data['date_depart'],
            date_return=self.forms['mrsrequest'].cleaned_data['date_return'],
        )

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


class MRSRequestUpdateView(MRSRequestFormViewMixin, generic.TemplateView):
    mrsrequest_uuid = None
    template_name = 'admin/mrsrequest/change_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return http.HttpResponseBadRequest()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = MRSRequest.objects.get(id=self.mrsrequest_uuid)
        self.pmt = self.object.pmt if self.object.pmt_id else None
        self.bills = self.object.bill_set.all()

        self.forms = collections.OrderedDict([
            ('mrsrequest', MRSRequestForm.factory(
                self, instance=self.object)),
            ('person', PersonForm.factory(
                self, instance=self.object.insured)),
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

        self.bills = self.bills_get_queryset()
        data = self.form_data()

        self.forms = collections.OrderedDict([
            ('mrsrequest', MRSRequestForm.factory(
                self, instance=self.object, data=data, files=data)),
            ('person', PersonForm.factory(
                self, instance=self.object.insured, data=request.POST)),
        ])

        with transaction.atomic():
            self.success = not self.form_errors() and self.save()

        return generic.TemplateView.get(self, request, *args, **kwargs)

    def save(self):
        self.pmt.mrsrequest = self.object
        self.pmt.save()
        self.bills.update(transport=self.transport)
        self.forms['person'].save()
        self.forms['mrsrequest'].save()
        self.forms['transport'].save()
        return True
