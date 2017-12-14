from django.urls import path

from mrsrequest.views import MRSFileDeleteView, MRSFileUploadView

from .models import PMT


urlpatterns = [
    path(
        '<pk>/delete',
        MRSFileDeleteView.as_view(model=PMT),
        name='pmt_delete'
    ),
    path(
        '<mrsrequest_uuid>/upload',
        MRSFileUploadView.as_view(model=PMT),
        name='pmt_upload'
    ),
]
