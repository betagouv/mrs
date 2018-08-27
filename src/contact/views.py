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

        Caller(
            callback='djcall.django.email_send',
            kwargs=dict(
                subject=template.loader.get_template(
                    'contact/team_mail_title.txt'
                ).render(dict(form=form)).strip(),
                body=template.loader.get_template(
                    'contact/team_mail_body.txt'
                ).render(dict(form=form)).strip(),
                to=[settings.TEAM_EMAIL],
                reply_to=[form.cleaned_data['email']],
            ),
        ).spool('mail')

        return generic.TemplateView.get(self, self.request)
