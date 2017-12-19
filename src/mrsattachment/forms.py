from django import forms

from django.urls import reverse


class MRSAttachmentField(forms.MultipleChoiceField):
    def __init__(self, upload=None, download=None, max_files=20, *a, **k):
        self.upload = upload
        self.download = download
        self.max_files = max_files

        k.setdefault(
            'widget',
            MRSAttachmentWidget(
                upload=self.upload,
                download=self.download,
            )
        )

        super().__init__(*a, **k)


class MRSAttachmentWidget(forms.FileInput):
    def __init__(self, upload, download, max_files=20):
        self.upload = upload
        self.download = download
        self.max_files = max_files
        super().__init__()

    @property
    def attrs(self):
        self._attrs = self._attrs or {}

        if getattr(self, 'view', False):
            # Should be set by MRSRequestFormMixin factory
            mrsrequest_uuid = getattr(self.view, 'mrsrequest_uuid', False)

            if mrsrequest_uuid:
                self._attrs.update({
                    'data-max-files': self.max_files,
                    'data-upload-url': reverse(
                        self.upload,
                        args=[mrsrequest_uuid]
                    )
                })

        return self._attrs

    @attrs.setter
    def attrs(self, value):
        self._attrs = value
