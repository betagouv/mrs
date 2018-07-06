import collections
import json

from crudlfap import crudlfap

from django import http
from django import template
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views import generic
from ipware import get_client_ip

from caisse.models import Caisse, Email
from caisse.forms import CaisseVoteForm
from person.forms import PersonForm
from mrsemail.models import EmailTemplate

from .forms import (
    CertifyForm,
    MRSRequestForm,
    MRSRequestCreateForm,
    MRSRequestRejectForm,
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
            ('mrsrequest', MRSRequestCreateForm(
                instance=self.object,
                initial=dict(caisse=request.GET.get('caisse', None)),
            )),
            ('person', PersonForm(
                initial={k: v for k, v in request.GET.items()})),
            ('transport', TransportIterativeForm()),
            ('certify', CertifyForm()),
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


class MRSRequestStatusMixin:
    controller = 'modal'
    action = 'click->modal#open'

    def form_valid(self):
        args = (self.request.user, self.log_action_flag)
        if hasattr(self, 'object'):
            self.object.update_status(*args)
        else:
            for obj in self.object_list:
                obj.update_status(*args)
        return super().form_valid()

    def get_log_message(self):
        for flag, label in self.model.STATUS_CHOICES:
            if flag == self.log_action_flag:
                return label


class MRSRequestValidateMixin(MRSRequestStatusMixin):
    form_class = MRSRequestForm
    view_label = 'Valider'
    material_icon = 'check_circle'
    color = 'green'
    log_action_flag = MRSRequest.STATUS_VALIDATED
    short_permission_code = 'validate'

    def mail_render(self, destination, part, mrsrequest=None):
        mrsrequest = mrsrequest or self.object
        return template.loader.get_template(
            'mrsrequest/{}_validation_mail_{}.txt'.format(
                destination, part
            )
        ).render(dict(object=mrsrequest or self.object)).strip()

    def mail_insured(self, mrsrequest=None):
        mrsrequest = mrsrequest or self.object
        email = EmailMessage(
            self.mail_render('insured', 'title', mrsrequest),
            self.mail_render('insured', 'body', mrsrequest),
            settings.DEFAULT_FROM_EMAIL,
            [(mrsrequest or self.object).insured.email],
        )
        email.send()

    def mail_liquidation(self, mrsrequest=None):
        mrsrequest = mrsrequest or self.object
        email = EmailMessage(
            self.mail_render('liquidation', 'title', mrsrequest),
            self.mail_render('liquidation', 'body', mrsrequest),
            settings.DEFAULT_FROM_EMAIL,
            [mrsrequest.caisse.liquidation_email],
            reply_to=[settings.TEAM_EMAIL],
            attachments=[mrsrequest.pmt.tuple()] + [
                bill.tuple() for bill in mrsrequest.bill_set.all()
            ]
        )
        email.send()


class MRSRequestValidateView(MRSRequestValidateMixin, crudlfap.ObjectFormView):
    menus = ['object', 'object_detail']
    template_name = 'mrsrequest/mrsrequest_validate.html'
    body_class = 'modal-fixed-footer'

    def get_allowed(self):
        if super().get_allowed():
            return self.object.status == self.model.STATUS_INPROGRESS

    def get_form_valid_message(self):
        return 'Demande n°{} validée'.format(self.object.display_id)

    def form_valid(self):
        resp = super().form_valid()
        self.mail_insured()
        self.mail_liquidation()
        return resp


class MRSRequestValidateObjectsView(
        MRSRequestValidateMixin, crudlfap.ObjectsFormView):

    def get_form_valid_message(self):
        return '{} demandes validée'.format(len(self.object_list))

    def form_valid(self):
        resp = super().form_valid()
        for obj in self.object_list:
            self.mail_insured(obj)
            self.mail_liquidation(obj)
        return resp


class MRSRequestRejectView(MRSRequestStatusMixin, crudlfap.ObjectFormView):
    form_class = MRSRequestRejectForm
    template_name = 'mrsrequest/mrsrequest_reject.html'
    view_label = 'Rejeter'
    material_icon = 'do_not_disturb_on'
    color = 'red'
    log_action_flag = MRSRequest.STATUS_REJECTED
    body_class = 'modal-fixed-footer'
    menus = ['object_detail']

    def get_allowed(self):
        if super().get_allowed():
            return self.object.status in (
                self.model.STATUS_NEW, self.model.STATUS_INPROGRESS
            )

    def reject_templates_json(self):
        context = template.Context({'display_id': self.object.display_id})
        templates = {
            i.pk: dict(
                subject=template.Template(i.subject).render(context),
                body=template.Template(i.body).render(context),
            ) for i in EmailTemplate.objects.all()
        }
        return json.dumps(templates)

    def form_valid(self):
        # set before calling super()
        self.log_message = str(self.form.cleaned_data['template'])
        self.object.reject_template = self.form.cleaned_data['template']
        resp = super().form_valid()
        self.object.save()

        email = EmailMessage(
            self.form.cleaned_data['subject'],
            self.form.cleaned_data['body'],
            settings.DEFAULT_FROM_EMAIL,
            [self.object.insured.email],
            reply_to=[settings.TEAM_EMAIL],
        )
        email.send()

        return resp

    def get_form_valid_message(self):
        return 'Demande n°{} rejetée'.format(self.object.display_id)


class MRSRequestProgressView(MRSRequestStatusMixin, crudlfap.ObjectFormView):
    form_class = MRSRequestForm
    template_name = 'mrsrequest/mrsrequest_progress.html'
    view_label = 'En cours de liquidation'
    title_submit = 'Oui'
    material_icon = 'playlist_add_check'
    color = 'green'
    log_action_flag = MRSRequest.STATUS_INPROGRESS
    short_permission_code = 'inprogress'
    menus = ['object_detail']

    def get_allowed(self):
        if super().get_allowed():
            return self.object.status == self.model.STATUS_NEW

    def get_form_valid_message(self):
        return 'Demande n°{} en cours de liquidation'.format(
            self.object.display_id
        )
