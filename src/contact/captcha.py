from django import forms

from threadlocals.threadlocals import get_current_request


HELP = """
Merci de résoudre cette équation pour verifier que vous n'êtes pas un robot !
""".strip()


class CaptchaField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.help_text = HELP

    def clean(self, value):
        if not value:
            raise forms.ValidationError('Merci de complêter ce champs')

        try:
            value = int(value)
        except ValueError:
            raise forms.ValidationError(
                f'Merci de saisir un nombre entier au lieu de "{value}"'
            )

        request = get_current_request()

        if sum(request.session['captcha']) != value:
            raise forms.ValidationError(
                f'"{value}" n\'est pas la bonne réponse, merci de réessayer',
            )

        return value
