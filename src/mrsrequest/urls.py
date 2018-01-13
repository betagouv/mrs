from django.urls import path

from mrsattachment.views import (
    MRSFileDeleteView,
    MRSFileDownloadView,
    MRSFileUploadView,
)

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
        'bill/<pk>/delete',
        MRSFileDeleteView.as_view(model=Bill),
        name='bill_destroy'
    ),
    path(
        'bill/<pk>/download',
        MRSFileDownloadView.as_view(model=Bill),
        name='bill_download'
    ),
    path(
        'bill/<mrsrequest_uuid>/upload',
        MRSFileUploadView.as_view(model=Bill),
        name='bill_upload'
    ),
    path(
        'pmt/<pk>/destroy',
        MRSFileDeleteView.as_view(model=PMT),
        name='pmt_destroy',
    ),
    path(
        'pmt/<pk>/download',
        MRSFileDownloadView.as_view(model=PMT),
        name='pmt_download'
    ),
    path(
        'pmt/<mrsrequest_uuid>/upload',
        MRSFileUploadView.as_view(model=PMT),
        name='pmt_upload'
    ),
]
