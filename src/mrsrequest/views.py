import collections

from django import http
from django import template
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views import generic

from person.forms import PersonForm

from .forms import CertifyForm, MRSRequestCreateForm
from .models import MRSRequest


class MRSRequestCreateView(generic.TemplateView):
    template_name = 'mrsrequest/form.html'

    def get(self, request, *args, **kwargs):
        self.object = MRSRequest()
        self.object.allow(request)
        self.mrsrequest_uuid = str(self.object.id)

        self.forms = collections.OrderedDict([
            ('mrsrequest', MRSRequestCreateForm(instance=self.object)),
            ('person', PersonForm()),
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

        self.forms = collections.OrderedDict([
            ('mrsrequest', MRSRequestCreateForm(
                request.POST,
                mrsrequest_uuid=self.mrsrequest_uuid
            )),
            ('person', PersonForm(request.POST)),
            ('certify', CertifyForm(request.POST)),
        ])

        with transaction.atomic():
            self.success = not self.form_errors() and self.save()

        return generic.TemplateView.get(self, request, *args, **kwargs)

    def save(self):
        self.forms['mrsrequest'].instance.insured = (
            self.forms['person'].get_or_create())
        self.object = self.forms['mrsrequest'].save()

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

    def form_errors(self):
        return [
            (form.errors, form.non_field_errors)
            for form in self.forms.values()
            if not form.is_valid()
        ]
