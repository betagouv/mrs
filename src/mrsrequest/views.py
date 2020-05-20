import collections
from datetime import datetime
import json

from django import http
from django import template
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views import generic
from djcall.models import Caller

from caisse.models import Email, Caisse, Region
from person.forms import PersonForm
from rating.forms import RatingForm
from rating.models import Rating

from mrs.settings import TITLE_SUFFIX

from .forms import (
    CertifyForm,
    MRSRequestCreateForm,
    TransportFormSet,
    TransportIterativeForm,
    # Deactivate email consent for now, not used anymore by staff
    # UseEmailForm,
)
from .models import today, Bill, MRSRequest, Transport


class MRSRequestFormBaseView(generic.TemplateView):
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


class MRSRequestCreateView(MRSRequestFormBaseView):
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

        self.forms = collections.OrderedDict([
            ('mrsrequest', MRSRequestCreateForm(
                instance=self.object,
            )),
            ('person', PersonForm(
                initial={k: v for k, v in request.GET.items()})),
            ('transport', TransportIterativeForm()),
            ('transport_formset', TransportFormSet()),
            ('certify', CertifyForm()),
            # Deactivate email consent for now, not used anymore by staff
            # ('use_email', UseEmailForm()),
        ])

        return super().get(request, *args, **kwargs)

    def caisses_json(self):
        caisses = {
            caisse.pk: dict(
                active=caisse.active,
                name=str(caisse),
                nopmt_enable=caisse.nopmt_enable,
                parking_enable=caisse.parking_enable,
                regions=[r.pk for r in caisse.regions.all()],
            ) for caisse in Caisse.objects.all()
        }
        return json.dumps(caisses)

    def regimes_speciaux_id(self):
        id_region = Region.objects.filter(
            name='Régimes Spéciaux').values('id')[0]

        return json.dumps(id_region)

    def has_perm(self, exists=False):
        if not self.mrsrequest_uuid:  # require mrsrequest_uuid on post
            return False

        # view is supposed to create a new request
        try:
            if exists:
                if not MRSRequest.objects.filter(id=self.mrsrequest_uuid):
                    return False
            else:
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

        if 'rating-score' in request.POST:
            return self.post_rating(request, *args, **kwargs)
        else:
            return self.post_mrsrequest(request, *args, **kwargs)

    def post_rating(self, request, *args, **kwargs):
        self.mrsrequest_uuid = self.request.POST.get(
            'rating-mrsrequest_uuid', None)
        if not self.has_perm(exists=True):
            return http.HttpResponseBadRequest()

        self.rating_form = RatingForm(request.POST, prefix='rating')
        self.rating_form.instance.mrsrequest = MRSRequest.objects.get(
            pk=self.mrsrequest_uuid
        )

        if self.rating_form.is_valid():
            with transaction.atomic():
                self.success_rating = self.rating_form.save()

        return generic.TemplateView.get(self, request, *args, **kwargs)

    def rating_show(self):
        requests = MRSRequest.objects.filter(
            insured=self.object.insured,
        )

        previous = Rating.objects.filter(
            mrsrequest__in=requests,
        ).order_by('-creation_datetime').first()

        if previous:
            requests = requests.filter(
                creation_datetime__gte=previous.creation_datetime
            )

        return requests.count() >= 5

    def post_mrsrequest(self, request, *args, **kwargs):
        if not self.has_perm():
            return http.HttpResponseBadRequest()

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

                if self.conflicts_count:
                    # also increment the daily stat !
                    Caller(
                        callback='mrsstat.models.increment',
                        kwargs=dict(
                            name='mrsrequest_count_conflicting',
                            count=1,
                            date=today(),
                            caisse=self.forms['mrsrequest'].cleaned_data.get(
                                'caisse').pk,
                            recalculate=['mrsrequest_count_resolved'],
                        ),
                    ).spool('stat')

                if self.rating_show():
                    self.rating_form = RatingForm(
                        prefix='rating',
                        initial=dict(mrsrequest_uuid=self.mrsrequest_uuid),
                    )

            else:
                # will be needed later on by save_mrsrequest to calculate the
                # number of conflicts that the user has resolved on their own
                # for this MRSRequest
                self.session.setdefault(
                    'conflicts_initial',
                    self.conflicts_count,
                )

                # also increment the daily stat if not done already !
                if 'conflicts_initial_incremented' not in self.session:
                    Caller(
                        callback='mrsstat.models.increment',
                        kwargs=dict(
                            name='mrsrequest_count_conflicted',
                            count=1,
                            date=today(),
                            caisse=self.forms['mrsrequest'].cleaned_data.get(
                                'caisse').pk,
                            recalculate=['mrsrequest_count_resolved'],
                        ),
                    ).spool('stat')
                    self.session['conflicts_initial_incremented'] = True

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
            # Deactivate email consent for now, not used anymore by staff
            # ('use_email', UseEmailForm(request.POST)),
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

        # Deactivate email consent for now, not used anymore by staff
        # if self.forms['use_email'].cleaned_data['use_email']:
        #     person.use_email = True

        person.save()

        mail_context = dict(view=self, base_url=settings.BASE_URL)
        Caller(
            callback='djcall.django.email_send',
            kwargs=dict(
                subject=template.loader.get_template(
                    'mrsrequest/success_mail_title.txt'
                ).render(mail_context).strip(),
                body=template.loader.get_template(
                    'mrsrequest/success_mail_body.txt'
                ).render(mail_context).strip(),
                to=[self.object.insured.email],
                reply_to=[self.object.caisse.liquidation_email],
            )
        ).spool('mail')

        return True

    def form_confirms(self):
        self.forms['transport_formset'].add_confirms(
            nir=self.forms['person'].cleaned_data['nir'],
            birth_date=self.forms['person'].cleaned_data['birth_date'],
        )
        return self.form_errors()


class MRSRequestUpdateBaseView(MRSRequestFormBaseView):
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object:
            self.template_name = 'mrsrequest/notfound.html'
            return generic.TemplateView.get(self, request, *args, **kwargs)

        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        try:
            return MRSRequest.objects.filter(
                pk=self.kwargs['pk'],
                token=self.kwargs['token'],
            ).first()
        except ValidationError:  # catch invalid uuids
            return None


class MRSRequestUpdateView(MRSRequestUpdateBaseView):
    template_name = 'mrsrequest/update.html'

    def get(self, request, *args, **kwargs):
        self.mrsrequest_uuid = str(self.object.id)

        self.forms = collections.OrderedDict([
            ('mrsrequest', MRSRequestCreateForm(
                mrsrequest_uuid=self.mrsrequest_uuid
            )),
            ('transport', TransportIterativeForm()),
            ('transport_formset', TransportFormSet()),
        ])

        return super().get(request, *args, **kwargs)


class MRSRequestCancelView(MRSRequestUpdateBaseView):
    template_name = 'mrsrequest/cancel.html'

    def post(self, request, *args, **kwargs):
        if self.object.status != self.object.STATUS_NEW:
            return http.HttpResponseBadRequest()

        self.object.status = self.object.STATUS_CANCELED
        self.object.status_datetime = datetime.now()
        self.object.save()

        self.object.logentries.create(
            action=MRSRequest.STATUS_CANCELED,
            comment='Annulation',
        )

        body = template.loader.get_template(
            'mrsrequest/cancelation_email.txt'
        ).render(dict(object=self.object, base_url=settings.BASE_URL)).strip()

        Caller(
            callback='djcall.django.email_send',
            kwargs=dict(
                subject=f'MRS: Annulation demande {self.object.display_id}',
                body=body.strip(),
                to=[self.object.insured.email],
                reply_to=[self.object.caisse.liquidation_email],
            )
        ).spool('mail')

        return generic.TemplateView.get(self, request, *args, **kwargs)
