import uuid

from django import http
from django.views import generic

from .forms import MRSRequestCreateForm
from .models import MRSRequest


class MRSRequestCreateView(generic.FormView):
    form_class = MRSRequestCreateForm
    template_name = 'mrsrequest/form.html'

    def post(self, request, *args, **kwargs):
        if 'id' not in request.POST:
            return http.HttpResponseBadRequest('Nous avons perdu le UUID')

        self.id = request.POST['id']
        self.object, created = MRSRequest.objects.get_or_create(
            id=self.id)
        if not self.object.is_allowed(request):
            return http.HttpResponseBadRequest()

        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.id = str(uuid.uuid4())
        MRSRequest(self.id).allow(request)
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        return dict(
            id=self.id,
        )

    def form_valid(self, form):
        return http.HttpResponseCreated('Merci!')


class MRSFileDeleteView(generic.DeleteView):
    '''AJAX File delete receiver view.'''

    def get_object(self):
        '''
        Use model.objects.allowed_objects(requset).

        This sets the base queryset which get_object() will use.
        '''
        try:
            return self.model.objects.allowed_objects(self.request).get(
                pk=self.kwargs['pk'])
        except self.model.DoesNotExist:
            raise http.Http404()

    def delete(self, request, *args, **kwargs):
        '''Delete the object and return OK response.'''
        self.object = self.get_object()
        self.object.delete()
        return http.HttpResponse()


class MRSFileUploadView(generic.View):
    '''AJAX File upload receiver view.'''
    model = None

    def post(self, request, *args, **kwargs):
        '''Verify uuid and call model.objects.record_upload().'''

        if 'mrsrequest_uuid' not in kwargs:
            return http.HttpResponseBadRequest('Nous avons perdu le UUID')
        mrsrequest_uuid = kwargs['mrsrequest_uuid']

        if not MRSRequest(id=mrsrequest_uuid).is_allowed(request):
            return http.HttpResponseBadRequest('Token de formulaire invalidé')

        if 'file' not in request.FILES:
            return http.HttpResponseBadRequest('Pas de fichier reçu')

        mrsrequest = MRSRequest.objects.get_or_create(id=mrsrequest_uuid)[0]
        upload = request.FILES['file']
        record = self.model.objects.record_upload(mrsrequest, upload)

        return http.JsonResponse(
            dict(deleteUrl=record.get_delete_url()),
            status=201,
        )
