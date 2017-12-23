from django import forms

from django.urls import reverse

from .settings import DEFAULT_MIME_TYPES


class MRSAttachmentField(forms.MultipleChoiceField):
    def __init__(self, upload=None, download=None, max_files=20,
                 mime_types=None, *a, **k):
        self.upload = upload
        self.download = download
        self.max_files = max_files
        self.mime_types = mime_types or DEFAULT_MIME_TYPES

        k.setdefault(
            'widget',
            type(
                'MRSAttachmentWidget', (MRSAttachmentWidget,),
                dict(field=self)
            )
        )

        super().__init__(*a, **k)


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
                    )
                })

        return self._attrs

    @attrs.setter
    def attrs(self, value):
        self._attrs = value
