import io

from django.db import models

from mrsrequest.models import MRSRequest

from .settings import DEFAULT_MIME_TYPES


class MRSAttachmentField(models.BinaryField):
    description = 'Binary attachment field'

    def __init__(self, upload=None, download=None, delete=None, max_files=20,
                 mime_types=None, *args, **kwargs):

        self.upload = upload
        self.download = download
        self.delete = delete
        self.max_files = max_files
        self.mime_types = mime_types or DEFAULT_MIME_TYPES

        # https://code.djangoproject.com/ticket/28937
        kwargs['editable'] = True

        models.Field.__init__(self, *args, **kwargs)

    def deconstruct(self):
        # https://code.djangoproject.com/ticket/28937#comment:3
        return models.Field.deconstruct(self)

    def value_from_object(self, obj):
        return obj.filename

    def save(self, name, content, save=True):
        pass

    def to_python(self, value):
        return []


class MRSAttachmentManager(models.Manager):
    def allowed_objects(self, request):
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
            filename=str(upload),
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

    objects = MRSAttachmentManager()

    @classmethod
    def get_upload_body(cls, upload):
        body = io.BytesIO()
        for chunk in upload.chunks():
            body.write(chunk)
        body.seek(0)  # rewind read point to beginning of registry
        return body.read()
