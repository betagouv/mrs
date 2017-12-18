from django.views import generic
from django.urls import include, path, reverse_lazy

from . import views


urlpatterns = [
    path(
        '',
        generic.RedirectView.as_view(
            url=reverse_lazy('mrsrequest:mrsrequest_list')
        ),
        name='index'
    ),
    path(
        'request/',
        include(views.MRSRequestViewSet().urls),
    ),
    path(
        'wizard/',
        views.MRSRequestCreateView.as_view(),
        name='wizard'
    ),
]
