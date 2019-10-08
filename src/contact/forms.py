import material
import re

from django import forms
from django import template
from django.conf import settings
from django.core import validators
from django.utils.translation import gettext as _

from caisse.forms import ActiveCaisseChoiceField
from captcha.fields import CaptchaField
from mrsrequest.models import MRSRequest

from .models import Contact


MOTIF_CHOICES = (
    (None, '---------'),
    ('request_error', "J'ai fait une erreur de saisie dans mon dossier"),
    ('request_question', "J'ai une question sur mon dossier"),
    ('website_question', "J'ai une idée d'amélioration pour votre site"),
    ('other', 'Autre sujet'),
)


class ContactForm(forms.Form):
    motif = forms.ChoiceField(
        label='Motif',
        choices=MOTIF_CHOICES,
    )
    caisse = ActiveCaisseChoiceField(
        otherchoice=False,
        label='Votre caisse de rattachement',
    )
    nom = forms.CharField()
    email = forms.EmailField()
    mrsrequest_display_id = forms.CharField(
        label='Numéro de demande (optionnel)',
        required=False,
        max_length=12,
        validators=[
            validators.RegexValidator(
                regex=r'^\d{12}$',
                message=_('MRSREQUEST_UNEXPECTED_DISPLAY_ID'),
            )
        ]
    )
    message = forms.CharField(widget=forms.Textarea)
    captcha = CaptchaField(required=True)

    layout = material.Layout(
        material.Fieldset(
            ' ',
            material.Row(
                'motif',
                'caisse',
            ),
            'mrsrequest_display_id',
            material.Row(
                'nom',
                'email',
            ),
            'message',
            'captcha',
        )
    )

    def clean_message(self):
        message = self.cleaned_data['message']

        if re.findall('https?://', message):
            raise forms.ValidationError(
                'Votre message ne doit pas contenir de lien.'
            )

        if '<' in message:
            raise forms.ValidationError(
                'Votre message ne doit pas contenir de chevrons.'
            )

        return message

    def get_email_kwargs(self):
        data = self.cleaned_data
        email = getattr(data['caisse'], 'liquidation_email', None)

        if email:
            to = [email]
        else:
            to = [settings.TEAM_EMAIL]

        if data['motif'].startswith('request'):
            subject = 'RÉCLAMATION MRS'

        else:
            subject = 'Nouveau message envoyé depuis le site mrs.beta.gouv.fr'

        body = template.loader.get_template(
            'contact/contact_mail_body.txt'
        ).render(dict(
            data=data,
            motif=dict(self.fields['motif'].choices)[data['motif']],
        )).strip()

        return dict(
            subject=subject,
            body=body,
            to=to,
            reply_to=[data['email']],
        )

    def save(self):
        instance = Contact(
            subject=self.cleaned_data['motif'],
            name=self.cleaned_data['nom'],
            email=self.cleaned_data['email'],
            message=self.cleaned_data['message'],
        )

        mid = self.cleaned_data['mrsrequest_display_id']
        if mid:
            mrs = MRSRequest.objects.filter(display_id=mid).first()
            if mrs:
                instance.mrsrequest = mrs

        caisse = self.cleaned_data['caisse']
        if caisse != 'other':
            instance.caisse = self.cleaned_data['caisse']

        instance.save()
        return instance
