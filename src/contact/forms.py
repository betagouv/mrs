import material

from django import forms
from django.core.mail import send_mail


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

    def form_valid(self, form):
        '''
        send_mail(
            template.loader.get_template(
                'contact/success_mail_title.txt'
            ).render(dict(form=form)).strip(),
            template.loader.get_template(
                'contact/success_mail_body.txt'
            ).render(dict(form=form)).strip(),
            settings.DEFAULT_FROM_EMAIL,
            [form.cleaned_data['email']],
        )
        '''
        return generic.TemplateView.get(self, self.request, *args, **kwargs)
