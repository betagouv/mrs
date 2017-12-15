from django import forms
from django.urls import reverse

from mrsrequest.forms import MRSRequestFormMixin


class MRSAttachmentWidget(forms.FileInput):
    def __init__(self, url_name, max_files=20):
        self.url_name = url_name
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
                        self.url_name,
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
        attrs = dict(view=view)

        attachment_fields = [
            name for name, field in cls.base_fields.items()
            if isinstance(field.widget, MRSAttachmentWidget)
        ]

        if view.request.method == 'POST':
            # Un-define fields with MRSAttachmentWidget from Form class
            # because it's dealt with in AJAX
            cls = type(
                cls.__name__,
                (cls,),
                {
                    field: None for field in attachment_fields
                }.update(attrs),
            )
        else:
            cls = type(cls.__name__, (cls,), attrs)

        form = cls(
            view.request.POST or None,
            prefix=cls.__name__.lower(),
        )

        for field in attachment_fields:
            form.fields[field].widget.view = view

        return form
