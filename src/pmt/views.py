from material.frontend.views import ModelViewSet

from .models import PMT


class PMTViewSet(ModelViewSet):
    model = PMT
