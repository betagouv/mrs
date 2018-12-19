from django import template
from django.conf import settings
from django.views import generic

from djcall.models import Caller

from .forms import ContactForm
from .forms import get_motif


def message_for_caisse(form):
    if form.cleaned_data.get('motif').startswith('request'):
        return True
    return False


class ContactView(generic.FormView):
    template_name = 'contact/form.html'
    form_class = ContactForm

    def form_valid(self, form):
        self.success = True

        subject = ""
        if message_for_caisse(form):
            subject = template.loader.get_template(
                'contact/team_mail_reclamation_mrs.txt'
            ).render().strip()
        else:
            subject = template.loader.get_template(
                'contact/team_mail_title.txt'
            ).render(dict(form=form)).strip()

        body = template.loader.get_template(
            'contact/team_mail_body.txt'
        ).render(dict(
            form=form,
            motif=get_motif(form.cleaned_data.get('motif')),
        )).strip()

        to = [settings.TEAM_EMAIL]
        if message_for_caisse(form):
            caisse = form.cleaned_data.get('caisse')
            to = [caisse.liquidation_email]

        Caller(
            callback='djcall.django.email_send',
            kwargs=dict(
                subject=subject,
                body=body,
                to=to,
                reply_to=[form.cleaned_data['email']],
            ),
        ).spool('mail')

        return generic.TemplateView.get(self, self.request)
