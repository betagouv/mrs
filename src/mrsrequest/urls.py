from django.urls import path

from mrsattachment.urls import factory

from .models import Bill, PMT
from . import views


app_name = 'mrsrequest'
urlpatterns = [
    path(
        'wizard/',
        views.MRSRequestCreateView.as_view(),
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
