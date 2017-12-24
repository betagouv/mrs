from django.urls import path

from mrsattachment.views import (
    MRSFileDeleteView,
    MRSFileDownloadView,
    MRSFileUploadView,
)

from .models import PMT


app_name = 'pmt'
urlpatterns = [
    path(
        '<pk>/destroy',
        MRSFileDeleteView.as_view(model=PMT),
        name='pmt_destroy',
    ),
    path(
        '<pk>/download',
        MRSFileDownloadView.as_view(model=PMT),
        name='pmt_download'
    ),
    path(
        '<mrsrequest_uuid>/upload',
        MRSFileUploadView.as_view(model=PMT),
        name='pmt_upload'
    ),
]
