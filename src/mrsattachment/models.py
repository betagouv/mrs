import io

from django.db import models

from . import forms
from .settings import DEFAULT_MIME_TYPES


class MRSAttachmentField(models.BinaryField):
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

    def formfield(self, **kwargs):
        kwargs.setdefault('upload', self.upload)
        kwargs.setdefault('mime_types', self.mime_types)
        kwargs.setdefault('download', self.download)
        kwargs.setdefault('max_files', self.max_files)
        kwargs.setdefault('label', self.verbose_name)
        kwargs.setdefault('help_text', self.help_text)
        return forms.MRSAttachmentField(**kwargs)

    def to_python(self, value):
        return []


class MRSAttachment(models.Model):
    filename = models.CharField(max_length=255)
    creation_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Heure d\'enregistrement du fichier')
    binary = MRSAttachmentField(
        verbose_name='Attachement')

    class Meta:
        abstract = True

    @classmethod
    def get_upload_body(cls, upload):
        body = io.BytesIO()
        for chunk in upload.chunks():
            body.write(chunk)
        body.seek(0)  # rewind read point to beginning of registry
        return body.read()
