from django.views import generic

from mrsrequest.views import MRSFileUploadMixin

from .models import PMT


class PMTDeleteView(generic.DeleteView):
    model = PMT
    # todo: def get_queryset to secure objects user can delete


class PMTUploadView(MRSFileUploadMixin, generic.View):
    def create_object(self):
        return PMT.objects.update_or_create(
            mrsrequest=self.mrsrequest,
            defaults=dict(
                filename=str(self.upload),
                binary=self.get_upload_body(self.upload),
            )
        )[0]
