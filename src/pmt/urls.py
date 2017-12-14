from django.urls import path

from . import views


urlpatterns = [
    path(
        '<pk>/delete',
        views.PMTUploadView.as_view(),
        name='pmt_delete'
    ),
    path(
        '<mrsrequest_uuid>/upload',
        views.PMTUploadView.as_view(),
        name='pmt_upload'
    ),
]
