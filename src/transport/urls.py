from django.urls import path

from mrsattachment.views import (
    MRSFileDeleteView,
    MRSFileDownloadView,
    MRSFileUploadView,
)

from .models import Bill


urlpatterns = [
    path(
        '<pk>/delete',
        MRSFileDeleteView.as_view(model=Bill),
        name='bill_delete'
    ),
    path(
        '<pk>/download',
        MRSFileDownloadView.as_view(model=Bill),
        name='bill_download'
    ),
    path(
        '<mrsrequest_uuid>/upload',
        MRSFileUploadView.as_view(model=Bill),
        name='bill_upload'
    ),
]
