from django import forms


class DateInput(forms.DateInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs'].setdefault('type', 'date')
        kwargs['attrs'].setdefault('placeholder', 'jj/mm/aaaa')
        super().__init__(*args, **kwargs)


class DateField(forms.DateField):
    def __init__(self, *args, **kwargs):
        # support both en and fr locales
        kwargs.setdefault('input_formats', ['%Y-%m-%d', '%d/%m/%Y'])
        kwargs.setdefault('widget', DateInput)
        super().__init__(*args, **kwargs)
