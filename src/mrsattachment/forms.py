from django import forms
from django.urls import reverse

from threadlocals.threadlocals import get_current_request

from mrsrequest.forms import MRSRequestFormMixin


class MRSAttachmentWidget(forms.FileInput):
    def __init__(self, url_name, max_files=20):
        self.url_name = url_name
        self.max_files = max_files
        super().__init__()

    @property
    def attrs(self):
        request = get_current_request()
        self._attrs = self._attrs or {}

        if request:
            self._attrs.update({
                'data-max-files': self.max_files,
                'data-upload-url': reverse(
                    self.url_name,
                    args=[request.mrsrequest_uuid]
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

        if view.request.method == 'POST':
            # Un-define fields with MRSAttachmentWidget from Form class
            # because it's dealt with in AJAX
            attachment_fields = [
                name for name, field in cls.base_fields.items()
                if isinstance(field.widget, MRSAttachmentWidget)
            ]

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

        return form
