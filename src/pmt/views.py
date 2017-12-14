from django.views import generic

from mrsrequest.views import MRSFileUploadMixin

from .models import PMT


class PMTDeleteView(generic.DeleteView):
    model = PMT
    # todo: def get_queryset to secure objects user can delete


class PMTUploadView(MRSFileUploadMixin, generic.View):
    def create_obj(self, mrsrequest, upload):
        return PMT.objects.update_or_create(
            mrsrequest=mrsrequest,
            defaults=dict(
                filename=str(upload),
                binary=self.get_upload_body(upload),
            )
        )[0]
