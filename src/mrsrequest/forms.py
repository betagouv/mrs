from django import forms
from django.views import generic

from .models import MRSRequest


class MRSRequestFormMixin(object):
    @classmethod
    def factory(cls, view, *args, **kwargs):
        if not isinstance(view, generic.View):
            raise Exception('First argument should be View instance')

        # Create a form subclass with the view instance
        cls = type(cls.__name__, (cls,), dict(view=view))

        kwargs.setdefault(
            'prefix', '{}'.format(cls.__name__.lower())
        )

        # The above made self.view available in the constructor
        form = cls(*args, **kwargs)

        for name, field in form.fields.items():
            # Joy
            form.fields[name].view = view
            form.fields[name].widget.view = view

        return form


class MRSRequestAdminForm(MRSRequestFormMixin, forms.ModelForm):
    class Meta:
        model = MRSRequest
        fields = ('status',)


class CertifyForm(MRSRequestFormMixin, forms.Form):
    CERTIFY_LABEL = ("J'atteste sur l'honneur l'exactitude des renseignements"
                     " portés ci-dessus")

    certify = forms.ChoiceField(
        choices=[(True, CERTIFY_LABEL)],
        label='Validation de la demande de remboursement',
        widget=forms.RadioSelect(),
        required=True,
    )
