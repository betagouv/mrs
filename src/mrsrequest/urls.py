from django.urls import path, reverse_lazy

from mrsattachment.views import MRSFileUploadView
from mrsattachment.urls import factory

from .models import Bill, BillVP, PMT
from . import views


app_name = 'mrsrequest'
urlpatterns = [
    path(
        'wizard/',
        views.generic.RedirectView.as_view(
            url=reverse_lazy('demande'), permanent=True),
        name='wizard'
    ),
]

urlpatterns += factory(PMT)
urlpatterns += factory(Bill)

for model in [BillVP]:
    name = model.__name__.lower()
    urlpatterns.append(
        path(
            f'{name}/<mrsrequest_uuid>/upload/',
            MRSFileUploadView.as_view(model=model),
            name=f'{name}_upload'
        )
    )
