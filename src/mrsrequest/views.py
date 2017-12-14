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
