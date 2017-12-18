from django.urls import path

from mrsattachment.views import (
    MRSFileDeleteView,
    MRSFileDownloadView,
    MRSFileUploadView,
)

from .models import PMT


urlpatterns = [
    path(
        '<pk>/delete',
        MRSFileDeleteView.as_view(model=PMT),
        name='pmt_delete'
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
