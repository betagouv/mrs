from django.views import generic

from djcall.models import Caller

from .forms import ContactForm


class ContactView(generic.FormView):
    template_name = 'contact/form.html'
    form_class = ContactForm

    def form_valid(self, form):
        Caller(
            callback='djcall.django.email_send',
            kwargs=form.get_email_kwargs(),
        ).spool('mail')
        form.save()
        self.success = True
        return generic.TemplateView.get(self, self.request)
