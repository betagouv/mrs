from django import template
from django.conf import settings
from django.core.mail import EmailMessage
from django.views import generic

from mrs.spooler import email_send

from .forms import ContactForm


class ContactView(generic.FormView):
    template_name = 'contact/form.html'
    form_class = ContactForm

    def form_valid(self, form):
        self.success = True

        email = EmailMessage(
            template.loader.get_template(
                'contact/team_mail_title.txt'
            ).render(dict(form=form)).strip(),
            template.loader.get_template(
                'contact/team_mail_body.txt'
            ).render(dict(form=form)).strip(),
            settings.DEFAULT_FROM_EMAIL,
            [settings.TEAM_EMAIL],
            reply_to=[form.cleaned_data['email']],
        )
        email_send(email)

        return generic.TemplateView.get(self, self.request)
