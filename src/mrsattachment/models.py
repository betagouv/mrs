import io

from django.db import models

from .settings import DEFAULT_MIME_TYPES


class MRSAttachmentManager(models.Manager):
    def allowed_objects(self, request):
        from mrsrequest.models import MRSRequest
        return self.filter(
            mrsrequest_uuid__in=MRSRequest.objects.allowed_uuids(request)
        )

    def recorded_uploads(self, mrsrequest_uuid):
        return self.model.objects.filter(mrsrequest_uuid=mrsrequest_uuid)

    def record_upload(self, mrsrequest_uuid, upload):
        '''
        Create a Bill object from the upload on the request's transport.

        When we want to support multiple forms in the future, we'll have a form
        number in the field_name attribute of the upload.
        '''
        return self.model.objects.create(
            mrsrequest_uuid=mrsrequest_uuid,
            filename=upload.name,
            mimetype=upload.content_type,
            binary=MRSAttachment.get_upload_body(upload),
        )


class MRSAttachment(models.Model):
    # This field is used when the document is uploaded
    mrsrequest_uuid = models.UUIDField()

    filename = models.CharField(max_length=255)
    creation_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Heure d\'enregistrement du fichier')
    binary = models.BinaryField(verbose_name='Attachement')
    mimetype = models.CharField(max_length=50, default='image/jpeg')

    objects = MRSAttachmentManager()

    def tuple(self):
        return (
            self.filename,
            self.binary,
            self.mimetype,
        )

    @classmethod
    def get_upload_body(cls, upload):
        body = io.BytesIO()
        for chunk in upload.chunks():
            body.write(chunk)
        body.seek(0)  # rewind read point to beginning of registry
        return body.read()
