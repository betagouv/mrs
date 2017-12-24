from django import forms

from django.urls import reverse

from .settings import DEFAULT_MIME_TYPES


class MRSAttachmentField(forms.ModelMultipleChoiceField):
    def __init__(self, model=None, upload=None, download=None, max_files=20,
                 mime_types=None, *a, **k):
        self.upload = upload
        self.download = download
        self.max_files = max_files
        self.mime_types = mime_types or DEFAULT_MIME_TYPES
        self.model = model

        k.setdefault(
            'widget',
            type(
                'MRSAttachmentWidget', (MRSAttachmentWidget,),
                dict(field=self)
            )
        )
        k.setdefault('queryset', self.model.objects.none())

        super().__init__(*a, **k)

    def clean(self, value):
        if self.required and not value:
            raise forms.ValidationError('Merci de choisir un fichier')
        return value

    def to_python(self, value):
        return value

    def prepare_value(self, value):
        return value


class MRSAttachmentWidget(forms.FileInput):
    @property
    def attrs(self):
        self._attrs = self._attrs or {}

        if getattr(self, 'view', False):
            # Should be set by MRSRequestFormMixin factory
            mrsrequest_uuid = getattr(self.view, 'mrsrequest_uuid', False)

            if mrsrequest_uuid:
                self._attrs.update({
                    'data-mime-types': ','.join(self.field.mime_types),
                    'data-max-files': self.field.max_files,
                    'data-upload-url': reverse(
                        self.field.upload,
                        args=[mrsrequest_uuid]
                    ),
                })

        if self.field.max_files > 1:
            self._attrs.setdefault('multiple', 'multiple')
        self._attrs.setdefault('name', 'file')

        return self._attrs

    @attrs.setter
    def attrs(self, value):
        self._attrs = value
