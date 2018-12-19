from django import template
from django.conf import settings
from django.views import generic

from djcall.models import Caller

from .forms import ContactForm


class ContactView(generic.FormView):
    template_name = 'contact/form.html'
    form_class = ContactForm

    def form_valid(self, form):
        self.success = True

        subject = ""
        if form.cleaned_data.get('motif').startswith('request'):
            subject = template.loader.get_template(
                'contact/team_mail_reclamation_mrs.txt'
            ).render().strip()
        else:
            subject = template.loader.get_template(
                'contact/team_mail_title.txt'
            ).render(dict(form=form)).strip()

        Caller(
            callback='djcall.django.email_send',
            kwargs=dict(
                subject=subject,
                body=template.loader.get_template(
                    'contact/team_mail_body.txt'
                ).render(dict(form=form)).strip(),
                to=[settings.TEAM_EMAIL],
                reply_to=[form.cleaned_data['email']],
            ),
        ).spool('mail')

        return generic.TemplateView.get(self, self.request)
