from django.urls import path

from . import views


app_name = 'mrsrequest'
urlpatterns = [
    path(
        'wizard/',
        views.MRSRequestCreateView.as_view(),
        name='wizard'
    ),
]
