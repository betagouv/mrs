import material

from django import forms


class ContactForm(forms.Form):
    nom = forms.CharField()
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)

    layout = material.Layout(
        material.Fieldset(
            'N\'hésitez pas à nous contacter !',
            material.Row(
                'nom',
                'email',
            ),
            'message',
        )
    )
