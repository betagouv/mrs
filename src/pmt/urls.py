from django.views import generic
from django.urls import include, path, reverse_lazy

from mrsattachment.views import (
    MRSFileDeleteView,
    MRSFileDownloadView,
    MRSFileUploadView,
)

from .views import PMTViewSet
from .models import PMT


urlpatterns = [
    path(
        '',
        generic.RedirectView.as_view(url=reverse_lazy('pmt:pmt_list')),
        name='index'
    ),
    path(
        'pmt/',
        include(PMTViewSet().urls),
    ),
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
