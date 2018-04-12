import collections
import json

from crudlfap import crudlfap

from django import http
from django import template
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from ipware import get_client_ip

from caisse.models import Email
from caisse.forms import CaisseVoteForm
from person.forms import PersonForm
from mrsemail.models import EmailTemplate

from .forms import (
    CertifyForm,
    MRSRequestCreateForm,
    MRSRequestRejectForm,
    MRSRequestValidateForm,
    TransportForm,
    TransportIterativeForm,
)
from .models import MRSRequest, Transport


class MRSRequestCreateView(generic.TemplateView):
    template_name = 'mrsrequest/form.html'
    base = 'base.html'

    def get(self, request, *args, **kwargs):
        self.object = MRSRequest()
        self.object.allow(request)
        self.mrsrequest_uuid = str(self.object.id)
        self.caisse_form = CaisseVoteForm(prefix='other')

        self.forms = collections.OrderedDict([
            ('mrsrequest', MRSRequestCreateForm(instance=self.object)),
            ('person', PersonForm(
                initial={k: v for k, v in request.GET.items()})),
            ('transport', TransportIterativeForm()),
            ('certify', CertifyForm()),
        ])

        return super().get(request, *args, **kwargs)

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
        self.forms['transport'] = TransportIterativeForm(
            instance=Transport(mrsrequest_id=self.mrsrequest_uuid),
        )

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

        self.forms = collections.OrderedDict([
            ('mrsrequest', MRSRequestCreateForm(
                request.POST,
                mrsrequest_uuid=self.mrsrequest_uuid
            )),
            ('person', PersonForm(request.POST)),
            ('certify', CertifyForm(request.POST)),
        ])
        self.forms['transport'] = TransportIterativeForm(
            request.POST,
            instance=Transport(mrsrequest_id=self.mrsrequest_uuid),
        )
        for key, value in self.request.POST.items():
            if '-date_return' not in key:
                continue

            number = key.split('-')[0]
            self.forms['transport-{}'.format(number)] = form = TransportForm(
                request.POST,
                instance=Transport(mrsrequest_id=self.mrsrequest_uuid),
                prefix=number,
            )
            form.fields['date_depart'].label += ' {}'.format(number)
            form.fields['date_return'].label += ' {}'.format(number)

        with transaction.atomic():
            self.success = not self.form_errors() and self.save_mrsrequest()

        return generic.TemplateView.get(self, request, *args, **kwargs)

    def save_mrsrequest(self):
        self.forms['mrsrequest'].instance.insured = (
            self.forms['person'].get_or_create())
        self.forms['mrsrequest'].instance.creation_ip = get_client_ip(
            self.request)[0]
        self.object = self.forms['mrsrequest'].save()
        self.forms['transport'].save()
        for name, form in self.forms.items():
            if 'transport-' not in name:
                continue
            form.save()

        email = EmailMessage(
            template.loader.get_template(
                'mrsrequest/success_mail_title.txt'
            ).render(dict(view=self)).strip(),
            template.loader.get_template(
                'mrsrequest/success_mail_body.txt'
            ).render(dict(view=self)).strip(),
            settings.DEFAULT_FROM_EMAIL,
            [self.object.insured.email],
            reply_to=[settings.TEAM_EMAIL],
        )
        email.send()

        return True

    def form_errors(self):
        return [
            (form.errors, form.non_field_errors)
            for form in self.forms.values()
            if not form.is_valid()
        ]


class MRSRequestAdminBaseView(crudlfap.UpdateView):
    menus = ['object_detail']

    def get_allowed(self):
        if super().get_allowed():
            return not self.object.status

    def form_valid(self, form):
        self.object.status_user = self.request.user
        self.object.status_datetime = timezone.now()
        return super().form_valid(form)


class MRSRequestValidateView(MRSRequestAdminBaseView):
    form_class = MRSRequestValidateForm
    template_name = 'mrsrequest/mrsrequest_validate.html'
    action_name = 'Valider'
    material_icon = 'check_circle'
    color = 'green'

    def get_mail_body(self):
        return template.loader.get_template(
            'mrsrequest/liquidation_validation_mail_body.txt',
        ).render(dict(object=self.object)).strip()

    def get_mail_title(self):
        return template.loader.get_template(
            'mrsrequest/liquidation_validation_mail_title.txt',
        ).render(dict(object=self.object)).strip()

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.info(self.request, 'Demande n°{} validée'.format(
            form.instance.display_id))

        email = EmailMessage(
            self.get_mail_title(),
            self.get_mail_body(),
            settings.DEFAULT_FROM_EMAIL,
            [self.object.caisse.liquidation_email],
            reply_to=[settings.TEAM_EMAIL],
            attachments=[self.object.pmt.tuple()] + [
                bill.tuple() for bill in self.object.bill_set.all()
            ]
        )
        email.send()

        return resp

    def get_success_url(self):
        return reverse('admin:mrsrequest_mrsrequest_changelist')


class MRSRequestRejectView(MRSRequestAdminBaseView):
    form_class = MRSRequestRejectForm
    template_name = 'mrsrequest/mrsrequest_reject.html'
    action_name = 'Rejeter'
    material_icon = 'do_not_disturb_on'
    color = 'red'

    def reject_templates_json(self):
        context = template.Context({'display_id': self.object.display_id})
        templates = {
            i.pk: dict(
                subject=template.Template(i.subject).render(context),
                body=template.Template(i.body).render(context),
            ) for i in EmailTemplate.objects.all()
        }
        return json.dumps(templates)

    def form_valid(self, form):
        resp = super().form_valid(form)

        self.object.reject_template = form.cleaned_data['template']
        self.object.save()

        messages.info(self.request, 'Demande n°{} rejetée'.format(
            form.instance.display_id))

        email = EmailMessage(
            form.cleaned_data['subject'],
            form.cleaned_data['body'],
            settings.DEFAULT_FROM_EMAIL,
            [self.object.insured.email],
            reply_to=[settings.TEAM_EMAIL],
        )
        email.send()

        return resp

    def get_success_url(self):
        return reverse('admin:mrsrequest_mrsrequest_changelist')
