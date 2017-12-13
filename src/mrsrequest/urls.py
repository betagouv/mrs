from django.urls import path

from . import views


urlpatterns = [
    path(
        'create/',
        views.MRSRequestCreateView.as_view(),
        name='mrsrequest_create'
    ),
]
