from material.frontend.views import ModelViewSet

from .models import Person


class PersonViewSet(ModelViewSet):
    model = Person
    list_display = ('first_name', 'last_name', 'birth_date', 'nir')
