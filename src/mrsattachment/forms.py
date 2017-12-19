from django import forms

from django.urls import reverse

from mrsrequest.forms import MRSRequestFormMixin


class MRSAttachmentField(forms.FileField):
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
        self.max_files = max_files
        super().__init__()

    @property
    def attrs(self):
        self._attrs = self._attrs or {}

        if getattr(self, 'view', False):
            # Should be set by MRSAttachementFormMixin.factory

            request = self.view.request
            mrsrequest_uuid = getattr(request, 'mrsrequest_uuid', False)

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


class MRSAttachementFormMixin(MRSRequestFormMixin):
    @classmethod
    def factory(cls, view):
        # List of field names which have widget=MRSAttachmentWidget
        attachment_fields = [
            name for name, field in cls.base_fields.items()
            if isinstance(field.widget, MRSAttachmentWidget)
        ]

        attrs = dict(view=view)
        if view.request.method == 'POST':
            # Un-define fields with MRSAttachmentWidget from Form class
            # because it's dealt with in AJAX
            attrs.update({
                field: None for field in attachment_fields
            })

        # Create a Form subclass on the fly with our attrs
        cls = type(cls.__name__, (cls,), attrs)

        # Instanciate our form subclass created above with a prefix for mixing
        # forms on the same page
        form = cls(
            view.request.POST if view.request.method == 'POST' else None,
            prefix=cls.__name__.lower(),
        )

        if view.request.method != 'POST':
            # Set field widget view attribute if we haven't canceled them above
            for field in attachment_fields:
                form.fields[field].widget.view = view

        return form
