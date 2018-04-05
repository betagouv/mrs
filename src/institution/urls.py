from django.urls import path

from mrs.views import StaticView
from . import views


app_name = 'institution'
urlpatterns = [
    path(
        '<finess>/mrsrequest/iframe/',
        views.InstitutionMRSRequestCreateView.as_view(),
        name='mrsrequest_iframe'
    ),
    path(
        '<finess>/mrsrequest/iframe/example/',
        views.InstitutionMRSRequestIframeExampleView.as_view(),
        name='mrsrequest_iframe_example'
    ),
    path(
        'example.jpg',
        StaticView.as_view(
            path='img/icones/burger.png',
            content_type='image/png',
            allow_origin='*',
        ),
        name='example_jpg',
    ),
    path(
        '<finess>/mrsrequest/<mrsrequest_uuid>/status/',
        views.InstitutionMRSRequestStatusView.as_view(),
        name='mrsrequest_status'
    ),
]
