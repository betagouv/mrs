from django.urls import path, reverse_lazy

from graphene_django.views import GraphQLView
from mrsattachment.urls import factory

from .models import Bill, PMT
from . import views


app_name = 'mrsrequest'
urlpatterns = [
    path(
        'wizard/',
        views.generic.RedirectView.as_view(
            url=reverse_lazy('demande'), permanent=True),
        name='wizard'
    ),
    path(
        '<pk>/reject/',
        views.MRSRequestRejectView.as_view(),
        name='reject'
    ),
    path(
        '<pk>/validate/',
        views.MRSRequestValidateView.as_view(),
        name='validate'
    ),
]

urlpatterns += factory(PMT)
urlpatterns += factory(Bill)
