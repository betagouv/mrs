from django import template
from django.conf import settings
from django.views import generic

from djcall.models import Caller

from .forms import ContactForm


def get_email_data(form):
    to = [settings.TEAM_EMAIL]

    if form.cleaned_data.get('motif').startswith('request'):
        subject = 'RÉCLAMATION MRS'
        email = getattr(form.cleaned_data['caisse'], 'liquidation_email', None)

        if email:  # in case caisse == 'other', let TEAM_EMAIL
            to = [email]
    else:
        subject = 'Nouveau message envoyé depuis le site'

    body = template.loader.get_template(
        'contact/contact_mail_body.txt'
    ).render(dict(
        form=form,
        motif=dict(form.fields['motif'].choices)[form.cleaned_data['motif']],
    )).strip()

    return dict(subject=subject, body=body, to=to)


class ContactView(generic.FormView):
    template_name = 'contact/form.html'
    form_class = ContactForm

    def form_valid(self, form):
        self.success = True

        email_data = get_email_data(form)
        email_data['reply_to'] = [form.cleaned_data['email']]

        Caller(
            callback='djcall.django.email_send',
            kwargs=email_data,
        ).spool('mail')

        return generic.TemplateView.get(self, self.request)
