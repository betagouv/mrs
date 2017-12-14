from django.urls import path

from mrsrequest.views import MRSFileDeleteView, MRSFileUploadView

from .models import Bill


urlpatterns = [
    path(
        '<pk>/delete',
        MRSFileDeleteView.as_view(model=Bill),
        name='bill_delete'
    ),
    path(
        '<mrsrequest_uuid>/upload',
        MRSFileUploadView.as_view(model=Bill),
        name='bill_upload'
    ),
]
