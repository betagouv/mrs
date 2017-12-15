from django import forms
from django.urls import reverse

from threadlocals.threadlocals import get_current_request

from mrsrequest.forms import MRSRequestFormMixin


class MRSAttachmentWidget(forms.FileInput):
    def __init__(self, url_name, max_files=20):
        self.url_name = url_name
        self.max_files = max_files
        super().__init__()

    def render(self, name, value, attrs=None, renderer=None):
        self.attrs = self.attrs or {}
        request = get_current_request()

        self.attrs.update({
            'data-max-files': self.max_files,
            'data-upload-url': reverse(
                self.url_name,
                args=[request.mrsrequest_uuid]
            )
        })

        return super().render(name, value, attrs=attrs, renderer=renderer)


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
