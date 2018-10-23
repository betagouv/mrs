from django import forms

from mrsemail.models import EmailTemplate


class EmailForm(forms.Form):
    template = forms.ModelChoiceField(
        EmailTemplate.objects.active(),
        label='Modèle d\'email',
        widget=forms.Select(attrs={
            'data-controller': 'emailtemplate',
            'data-action': 'change->emailtemplate#change',
        }),
    )
    subject = forms.CharField(label='Sujet')
    body = forms.CharField(widget=forms.Textarea, label='Corps')
