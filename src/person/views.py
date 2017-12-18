from material.frontend.views import ModelViewSet

from .models import Person


class PersonViewSet(ModelViewSet):
    model = Person
