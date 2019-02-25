from django import forms


from .models import Rating


class ScoreWidget(forms.RadioSelect):
    def __init__(self, attrs=None, choices=()):
        attrs = attrs or dict()
        choices = [(i, i) for i in range(1, 11)]
        super().__init__(attrs, choices)


class RatingForm(forms.ModelForm):
    score = forms.IntegerField(
        min_value=1,
        max_value=10,
        widget=ScoreWidget,
    )
    comment = forms.CharField(
        label='Votre commentaire',
        required=False,
        widget=forms.Textarea,
    )

    # do not trust this field, it's used for javascript and checked
    # by the view for permission against the request session, but is
    # NOT to be trusted as input: don't use data['mrsrequest_uuid'] nor
    # cleaned_data['mrsrequest_uuid'], you've been warned.
    mrsrequest_uuid = forms.CharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Rating
        fields = ('score', 'comment', 'mrsrequest_uuid')
