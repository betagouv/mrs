from material.frontend.views import ModelViewSet

from .models import PMT


class PMTViewSet(ModelViewSet):
    model = PMT
    list_display = ('mrsrequest', 'filename', 'creation_datetime')
