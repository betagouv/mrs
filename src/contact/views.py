import random

from django.views import generic

from djcall.models import Caller

from .forms import ContactForm


class ContactView(generic.FormView):
    template_name = 'contact/form.html'
    form_class = ContactForm

    def get_form(self):
        if 'captcha' not in self.request.session:
            self.request.session['captcha'] = (
                random.randint(1, 9),
                random.randint(1, 9),
            )

        form = super().get_form()
        form.fields['captcha'].label = ' '.join(map(str, [
            'Combien font',
            self.request.session['captcha'][0],
            '+',
            self.request.session['captcha'][1],
            '?',
        ]))

        return form

    def form_valid(self, form):
        Caller(
            callback='djcall.django.email_send',
            kwargs=form.get_email_kwargs(),
        ).spool('mail')
        form.save()
        self.request.session.pop('captcha')
        self.success = True
        return generic.TemplateView.get(self, self.request)
