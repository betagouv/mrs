import io

from django import http
from django.views import generic

from jfu.http import UploadResponse

from mrsrequest.models import MRSRequest


class MRSFileDetailViewMikin(object):
    def get_object(self):
        '''
        Use model.objects.allowed_objects(requset).

        This sets the base queryset which get_object() will use.
        '''
        user = getattr(self.request, 'user', None)
        if user and user.is_staff:
            return self.model.objects.get(pk=self.kwargs['pk'])

        try:
            return self.model.objects.allowed_objects(self.request).get(
                pk=self.kwargs['pk'])
        except self.model.DoesNotExist:
            raise http.Http404()


class MRSFileDownloadView(MRSFileDetailViewMikin, generic.DetailView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        f = io.BytesIO(self.object.binary)
        content_type = self.object.mimetype or 'application/octet-stream'
        response = http.FileResponse(f, content_type=content_type)
        response['Content-Length'] = len(self.object.binary)
        if self.object.encoding:
            response['Content-Encoding'] = self.object.encoding
        return response


class MRSFileDeleteView(MRSFileDetailViewMikin, generic.DeleteView):
    '''
    AJAX File delete receiver view.

    This requires the model manager to have an allowed_objects() method taking
    a request object argument and returning a queryset of objects which the
    user is allowed to delete, it will then get the object from the queryset
    using the pk argument. Define your URL as such::

        path(
            '<pk>/delete',
            MRSFileDeleteView.as_view(model=YourModel),
            name='yourmodel_delete'
        ),

    Note that this should require a request to be allowed for the
    mrsrequest_uuid via the ``MRSRequest.allow(request)`` call, but it's left
    at the discretion of the developer to use
    ``MRSRequest.objects.allowed_objects()`` in their ``allowed_objects()``
    implementation.
    '''

    def delete(self, request, *args, **kwargs):
        '''Delete the object and return OK response.'''
        self.object = self.get_object()
        self.object.delete()
        return http.HttpResponse()


class MRSFileUploadView(generic.View):
    '''
    AJAX File upload receiver view.

    This requires the model manager to have an record_upload() method taking
    an MRSRequest object argument and a FormFile argument which must insert the
    object in the database and return it. Define your URL as such::

        path(
            '<mrsrequest_uuid>/upload',
            MRSFileUploadView.as_view(model=YourModel),
            name='yourmodel_upload'
        ),

    The object also needs a get_delete_url() method which will be returned in
    the response payload.

    Note that this requires a request to be allowed for the mrsrequest_uuid via
    the ``MRSRequest.allow(request)`` call.
    '''
    model = None

    def post(self, request, *args, **kwargs):
        '''Verify uuid and call model.objects.record_upload().'''

        if 'mrsrequest_uuid' not in kwargs:
            return http.HttpResponseBadRequest('Nous avons perdu le UUID')
        mrsrequest_uuid = kwargs['mrsrequest_uuid']

        if not MRSRequest(id=mrsrequest_uuid).is_allowed(request):
            return http.HttpResponseBadRequest('Token de formulaire invalide')

        if not request.FILES:
            return http.HttpResponseBadRequest('Pas de fichier reçu')

        # need to reverse engineer some action now to finish specs because our
        # mock object doesn't simulate all attributes
        # todo: validate filesize
        # todo: validate mimetype

        files = []
        for key, upload in request.FILES.items():
            record = self.model.objects.record_upload(mrsrequest_uuid, upload)
            files.append(dict(
                name=record.filename,
                url=record.get_download_url(),
                thumbnailUrl=record.get_download_url(),
                deleteUrl=record.get_delete_url(),
                deleteType='DELETE',
            ))

        return UploadResponse(request, files)
