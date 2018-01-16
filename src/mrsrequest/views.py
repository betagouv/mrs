import collections
import json

from django import http
from django import template
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.views import generic

from person.forms import PersonForm

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

    def get(self, request, *args, **kwargs):
        self.object = MRSRequest()
        self.object.allow(request)
        self.mrsrequest_uuid = str(self.object.id)

        self.forms = collections.OrderedDict([
            ('mrsrequest', MRSRequestCreateForm(instance=self.object)),
            ('person', PersonForm()),
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
        if not self.has_perm():
            return http.HttpResponseBadRequest()

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
            self.success = not self.form_errors() and self.save()

        return generic.TemplateView.get(self, request, *args, **kwargs)

    def save(self):
        self.forms['mrsrequest'].instance.insured = (
            self.forms['person'].get_or_create())
        self.object = self.forms['mrsrequest'].save()
        self.forms['transport'].save()
        for name, form in self.forms.items():
            if 'transport-' not in name:
                continue
            form.save()

        # refresh to get generated form_id
        self.object.refresh_from_db()

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


class MRSRequestAdminBaseView(generic.UpdateView):
    model = MRSRequest

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return http.HttpResponseRedirect(
                '{}?next={}'.format(
                    reverse('admin:login'),
                    request.get_full_path(),
                )
            )
        return super().dispatch(request, *args, **kwargs)


class MRSRequestValidateView(MRSRequestAdminBaseView):
    form_class = MRSRequestValidateForm
    template_name = 'mrsrequest/mrsrequest_validate.html'
    action_name = 'Valider'

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
            form.instance.verbose_id))

        email = EmailMessage(
            self.get_mail_title(),
            self.get_mail_body(),
            settings.DEFAULT_FROM_EMAIL,
            [settings.LIQUIDATION_EMAIL],
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

    def reject_templates_json(self):
        templates = {
            k: template.loader.get_template(
                'mrsrequest/mrsrequest_reject_{}.txt'.format(v)
            ).render()
            for k, v in (
                (self.form_class.REASON_OTHER, 'other'),
                (self.form_class.REASON_MISSING, 'missing'),
                (self.form_class.REASON_UNREADABLE, 'unreadable'),
            )
        }
        return json.dumps(templates)

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.info(self.request, 'Demande n°{} rejetée'.format(
            form.instance.verbose_id))

        email = EmailMessage(
            'Problème avec votre demande de remboursement MRS n°{}'.format(
                form.instance.verbose_id),
            form.cleaned_data['mail_body'],
            settings.DEFAULT_FROM_EMAIL,
            [self.object.insured.email],
            reply_to=[settings.TEAM_EMAIL],
        )
        email.send()

        return resp

    def get_success_url(self):
        return reverse('admin:mrsrequest_mrsrequest_changelist')
