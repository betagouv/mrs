import collections
import json

from django import http
from django import template
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views import generic
from django.urls import reverse

from djcall.models import Caller

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

            # beware that form_confirms will provision forms with artificial
            # errors: do NOT call it if confirmed was POST-ed
            if confirmed or not self.form_confirms():
                with transaction.atomic():
                    self.save_mrsrequest()
                    self.success = True
            else:
                # will be needed later on by save_mrsrequest to calculate the
                # number of conflicts that the user has resolved on their own
                # for this MRSRequest
                self.session.setdefault(
                    'conflicts_initial',
                    self.conflicts_count,
                )

                # trigger session backend write by session middleware
                self.request.session.modified = True

                self.confirm = True

        return generic.TemplateView.get(self, request, *args, **kwargs)

    @property
    def session(self):
        """Return a reference to the session dict for this MRSRequest."""
        return self.request.session.get(
            MRSRequest.SESSION_KEY
        ).get(
            self.mrsrequest_uuid
        )

    @property
    def conflicts_initial(self):
        return self.session.get('conflicts_initial', 0)

    @property
    def conflicts_count(self):
        '''
        return self.forms.get(
                'transport_formset'
            ).get_confirms_count()
        '''
        if '_conflicts_count' not in self.__dict__:
            self._conflicts_count = self.forms.get(
                'transport_formset'
            ).get_confirms_count()
        return self._conflicts_count

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
        mrsrequest = self.forms['mrsrequest'].instance

        self.forms['transport_formset'].set_confirms(
            person.nir, person.birth_date
        )
        conflicts_resolved = self.conflicts_initial - self.conflicts_count
        mrsrequest.conflicts_accepted = self.conflicts_count
        mrsrequest.conflicts_resolved = conflicts_resolved

        mrsrequest.insured = person
        self.object = self.forms['mrsrequest'].save()

        for form in self.forms['transport_formset'].forms:
            Transport.objects.create(
                date_depart=form.cleaned_data.get('date_depart'),
                date_return=form.cleaned_data.get('date_return'),
                mrsrequest=self.object,
            )

        if self.forms['use_email'].cleaned_data['use_email']:
            person.use_email = True

        person.conflicts_accepted += self.conflicts_count
        person.conflicts_resolved += conflicts_resolved
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

class MRSRequestCancelView(generic.TemplateView):
    template_name = 'mrsrequest/cancel.html'
    base = 'base.html'
    extra_context = {
        'title_suffix': TITLE_SUFFIX,
    }

    def get_context_data(self, **kwargs):
        update_token = kwargs.pop('update_token')
        requests = MRSRequest.objects.filter(update_token=update_token)
        context = super().get_context_data(**kwargs)

        if not requests.count():
            context['does_not_exist'] = True
            return context

        mrsrequest = requests.first()

        if mrsrequest.status == MRSRequest.STATUS_NEW:
            context['object'] = mrsrequest
        else:
            context['too_late'] = True

        return context

    def post(self, request, *args, **kwargs):
        update_token = kwargs.pop('update_token')
        requests = MRSRequest.objects.filter(update_token=update_token)

        if not requests.count():
            return

        mrsrequest = requests.first()
        if mrsrequest:
            deleted, _ = mrsrequest.delete()

            if deleted:
                return http.HttpResponseRedirect(
                    reverse('demande'))
            else:
                pass  # ajax message
