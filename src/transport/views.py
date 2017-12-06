from django.views import generic

from .forms import TransportCreateForm
from .models import Transport


class TransportCreateView(generic.CreateView):
    form_class = TransportCreateForm
    model = Transport
