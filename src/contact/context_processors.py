from .forms import ContactForm


def contact_form(request):
    return dict(new_contact_form=ContactForm())
