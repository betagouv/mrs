from django import forms

import material


class MRSRequestFormMixin(object):
    @classmethod
    def factory(cls, view):
        return cls(
            view.request.POST or None,
            prefix=cls.__name__.lower(),
        )


class CertifyForm(MRSRequestFormMixin, forms.Form):
    CERTIFY_LABEL = ("J'atteste sur l'honneur l'exactitude des renseignements"
                     " portés ci-dessus")

    certify = forms.ChoiceField(
        choices=[(True, CERTIFY_LABEL)],
        label='Validation de la demande de remboursement',
        widget=forms.RadioSelect(),
        required=True,
    )
