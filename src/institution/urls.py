from django.urls import path

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
        '<finess>/mrsrequest/<mrsrequest_uuid>/status/',
        views.InstitutionMRSRequestStatusView.as_view(),
        name='mrsrequest_status'
    ),
]
