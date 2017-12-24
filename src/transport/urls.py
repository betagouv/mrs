from django.urls import path

from mrsattachment.views import (
    MRSFileDeleteView,
    MRSFileDownloadView,
    MRSFileUploadView,
)

from .models import Bill


app_name = 'transport'
urlpatterns = [
    path(
        '<pk>/delete',
        MRSFileDeleteView.as_view(model=Bill),
        name='bill_destroy'
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
