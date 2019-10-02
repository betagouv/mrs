import mimetypes

from os.path import splitext
from uuid import uuid4

from django.db import models
from django.core.files.storage import FileSystemStorage
from django.dispatch import receiver

from mrs.settings import ATTACHMENT_ROOT


class MRSAttachmentManager(models.Manager):
    def allowed_objects(self, request):
        from mrsrequest.models import MRSRequest
        return self.filter(
            mrsrequest_uuid__in=MRSRequest.objects.allowed_uuids(request)
        )

    def recorded_uploads(self, mrsrequest_uuid):
        return self.model.objects.filter(mrsrequest_uuid=mrsrequest_uuid)

    def record_upload(self, mrsrequest_uuid, upload, **kwargs):
        '''
        Create a Bill object from the upload on the request's transport.

        When we want to support multiple forms in the future, we'll have a form
        number in the field_name attribute of the upload.
        '''
        return self.model.objects.create(
            mrsrequest_uuid=mrsrequest_uuid,
            filename=upload.name,
            attachment_file=upload,
            **kwargs
        )


class MRSAttachment(models.Model):
    # This field is used when the document is uploaded
    mrsrequest_uuid = models.UUIDField()

    upload_storage = FileSystemStorage(
        location=ATTACHMENT_ROOT,
    )

    def attachment_file_path(self, filename):
        # file will be uploaded to ATTACHMENT_UPLOAD_ROOT/
        # <mrsrequest_uuid>-<uuid>-<filename>
        return '{0}-{1}{2}'.format(
            self.mrsrequest_uuid,
            uuid4(),
            splitext(filename)[-1]
        )

    filename = models.CharField(max_length=255)
    creation_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Heure d\'enregistrement du fichier')
    attachment_file = models.FileField(
        upload_to=attachment_file_path,
        storage=upload_storage,
        verbose_name='Attachement',
        default="",
        null=True
    )

    objects = MRSAttachmentManager()

    @property
    def encoding(self):
        return mimetypes.guess_type(self.filename)[1]

    @property
    def mimetype(self):
        return mimetypes.guess_type(self.filename)[0]

    def tuple(self):
        return (
            self.filename,
            self.attachment_file.name,
            self.mimetype,
        )


@receiver(models.signals.post_delete, sender=MRSAttachment)
def auto_delete_attachment_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MRSAttachment` object is deleted.
    """
    if instance.attachment_file:
        instance.attachment_file.delete()
