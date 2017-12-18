from django.views import generic
from django.urls import include, path, reverse_lazy

from . import views


urlpatterns = [
    path(
        '',
        generic.RedirectView.as_view(url=reverse_lazy('person:person_list')),
        name='index'
    ),
    path(
        'person/',
        include(views.PersonViewSet().urls),
    ),
]
