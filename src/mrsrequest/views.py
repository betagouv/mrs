from django.views import generic

from .forms import MRSRequestCreateForm


class MRSRequestCreateView(generic.FormView):
    form_class = MRSRequestCreateForm
    template_name = 'form.html'
