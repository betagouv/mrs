from django.views import generic
from django.urls import include, path, reverse_lazy

from mrsattachment.views import (
    MRSFileDeleteView,
    MRSFileDownloadView,
    MRSFileUploadView,
)

from .views import (
    BillViewSet,
    TransportViewSet,
)

from .models import Bill


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
    path(
        '',
        generic.RedirectView.as_view(
            url=reverse_lazy('transport:transport_list')
        ),
        name='index'
    ),
    path(
        'transport/',
        include(TransportViewSet().urls),
    ),
    path(
        'bill/',
        include(BillViewSet().urls),
    ),
]
