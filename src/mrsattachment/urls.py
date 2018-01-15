from django.urls import path

from mrsattachment.views import (
    MRSFileDeleteView,
    MRSFileDownloadView,
    MRSFileUploadView,
)


def factory(model):
    '''Generate urls for an MRSAttachment model.'''
    name = model._meta.model_name

    return [
        path(
            '{}/<pk>/delete/'.format(name),
            MRSFileDeleteView.as_view(model=model),
            name='{}_destroy'.format(name)
        ),
        path(
            '{}/<pk>/download/'.format(name),
            MRSFileDownloadView.as_view(model=model),
            name='{}_download'.format(name)
        ),
        path(
            '{}/<mrsrequest_uuid>/upload/'.format(name),
            MRSFileUploadView.as_view(model=model),
            name='{}_upload'.format(name)
        ),
    ]
