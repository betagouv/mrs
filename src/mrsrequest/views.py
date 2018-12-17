import collections
import json

from django import http
from django import template
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views import generic
from djcall.models import Caller
from ipware import get_client_ip

from caisse.models import Caisse, Email
from caisse.forms import CaisseVoteForm
from person.forms import PersonForm

from mrs.settings import TITLE_SUFFIX

from .forms import (
    CertifyForm,
    MRSRequestCreateForm,
    TransportFormSet,
    TransportIterativeForm,
    UseEmailForm,
)
from .models import Bill, MRSRequest, Transport


class MRSRequestCreateView(generic.TemplateView):
    template_name = 'mrsrequest/form.html'
    base = 'base.html'
    modes = [i[0] for i in Bill.MODE_CHOICES]
    extra_context = {
        'title_suffix': TITLE_SUFFIX,
    }

    def get(self, request, *args, **kwargs):
        self.object = MRSRequest()
        self.object.allow(request)
        self.mrsrequest_uuid = str(self.object.id)
        self.caisse_form = CaisseVoteForm(prefix='other')

        self.forms = collections.OrderedDict([
            ('mrsrequest', MRSRequestCreateForm(
                instance=self.object,
                initial=dict(caisse=request.GET.get('caisse', None)),
            )),
            ('person', PersonForm(
                initial={k: v for k, v in request.GET.items()})),
            ('transport', TransportIterativeForm()),
            ('transport_formset', TransportFormSet()),
            ('certify', CertifyForm()),
            ('use_email', UseEmailForm()),
        ])

        return super().get(request, *args, **kwargs)

    def caisses_json(self):
        caisses = {
            i.pk: dict(
                parking_enable=i.parking_enable,
            ) for i in Caisse.objects.all()
        }
        return json.dumps(caisses)

    def has_perm(self):
        if not self.mrsrequest_uuid:  # require mrsrequest_uuid on post
            return False

        # view is supposed to create a new request
        try:
            if MRSRequest.objects.filter(id=self.mrsrequest_uuid):
                return False
        except ValidationError:  # badly formated uuid
            return False

        # Let's not even load the object from db if request aint allowed
        if not MRSRequest(id=self.mrsrequest_uuid).is_allowed(self.request):
            return False

        return True

    def post(self, request, *args, **kwargs):
        self.mrsrequest_uuid = self.request.POST.get('mrsrequest_uuid', None)
        caisse = request.POST.get('caisse', None)

        if caisse == 'other':
            return self.post_caisse(request, *args, **kwargs)
        else:
            return self.post_mrsrequest(request, *args, **kwargs)

    def post_caisse(self, request, *args, **kwargs):
        # needed for rendering
        self.forms = collections.OrderedDict([
            ('mrsrequest', MRSRequestCreateForm(
                initial={'caisse': 'other'},
                mrsrequest_uuid=self.mrsrequest_uuid
            )),
            ('person', PersonForm()),
            ('certify', CertifyForm()),
        ])
        self.forms['transport'] = TransportIterativeForm()
        self.forms['transport_formset'] = TransportFormSet()

        self.caisse_form = CaisseVoteForm(request.POST, prefix='other')
        with transaction.atomic():
            self.success_caisse = (
                self.caisse_form.is_valid() and self.save_caisse())

        return generic.TemplateView.get(self, request, *args, **kwargs)

    def save_caisse(self):
        caisse = self.caisse_form.cleaned_data['caisse']

        email = self.caisse_form.cleaned_data.get('email', None)
        if email:
            Email.objects.create(email=email, caisse=caisse)

        caisse.score += 1
        caisse.save()

        return True

    def post_mrsrequest(self, request, *args, **kwargs):
        if not self.has_perm():
            return http.HttpResponseBadRequest()

        # for display
        self.caisse_form = CaisseVoteForm(prefix='other')

        self.forms = self.post_get_forms(request)

        self.success = self.confirm = False
        if not self.form_errors():
            confirmed = self.request.POST.get('confirm', False)

            if confirmed or not self.form_confirms():
                with transaction.atomic():
                    self.save_mrsrequest()
                    self.success = True
            else:
                self.confirm = True

        return generic.TemplateView.get(self, request, *args, **kwargs)

    def post_get_forms(self, request):
        forms = collections.OrderedDict([
            ('mrsrequest', MRSRequestCreateForm(
                request.POST,
                mrsrequest_uuid=self.mrsrequest_uuid
            )),
            ('person', PersonForm(request.POST)),
            ('certify', CertifyForm(request.POST)),
            ('use_email', UseEmailForm(request.POST)),
        ])
        forms['transport'] = TransportIterativeForm(request.POST)
        forms['transport_formset'] = TransportFormSet(request.POST)

        return forms

    def save_mrsrequest(self):
        person = self.forms['person'].get_or_create()
        self.forms['transport_formset'].set_confirms(
            person.nir, person.birth_date
        )
        for form in self.forms['transport_formset'].forms:
            for field, kinds in form.confirms.items():
                person.confirms += len(kinds)

        self.forms['mrsrequest'].instance.insured = person
        self.forms['mrsrequest'].instance.creation_ip = get_client_ip(
            self.request)[0]
        self.object = self.forms['mrsrequest'].save()
        if self.forms['use_email'].cleaned_data['use_email']:
            person.use_email = True

        for form in self.forms['transport_formset'].forms:
            Transport.objects.create(
                date_depart=form.cleaned_data.get('date_depart'),
                date_return=form.cleaned_data.get('date_return'),
                mrsrequest=self.object,
            )
        person.save()

        Caller(
            callback='djcall.django.email_send',
            kwargs=dict(
                subject=template.loader.get_template(
                    'mrsrequest/success_mail_title.txt'
                ).render(dict(view=self)).strip(),
                body=template.loader.get_template(
                    'mrsrequest/success_mail_body.txt'
                ).render(dict(view=self)).strip(),
                to=[self.object.insured.email],
                reply_to=[settings.TEAM_EMAIL],
            )
        ).spool('mail')

        return True

    def form_errors(self):
        return [
            (form.errors, getattr(form, 'non_field_errors', []))
            for form in self.forms.values()
            if not form.is_valid()
        ]

    def form_confirms(self):
        self.forms['transport_formset'].add_confirms(
            nir=self.forms['person'].cleaned_data['nir'],
            birth_date=self.forms['person'].cleaned_data['birth_date'],
        )
        return self.form_errors()
