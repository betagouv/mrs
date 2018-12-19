import material

from django import forms

from caisse.forms import ActiveCaisseChoiceField

class ContactForm(forms.Form):
    motif = forms.ChoiceField(
        label='Motif',
        choices=(
            (None, '---------'),
            ('request_error', 'Erreur dans votre demande'),
            ('request_question', 'Réclamation sur votre demande'),
            ('website_question', 'Question sur le site'),
            ('other', 'Autre'),
        ),
    )
    caisse = ActiveCaisseChoiceField(
        label='Votre caisse de rattachement',
    )
    nom = forms.CharField()
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)

    layout = material.Layout(
        material.Fieldset(
            ' ',
            'motif',
            'caisse',
            material.Row(
                'nom',
                'email',
            ),
            'message',
        )
    )
