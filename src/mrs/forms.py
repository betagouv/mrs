from django import forms


class DateInput(forms.DateInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs'].setdefault('placeholder', 'jj/mm/aaaa')
        super().__init__(*args, **kwargs)


class DateInputNative(DateInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs'].setdefault('type', 'date')
        super().__init__(*args, **kwargs)


class DateField(forms.DateField):
    DEFAULT_HELP = 'Au format jj/mm/aaaa, exemple: 31/12/2000'

    def __init__(self, *args, **kwargs):
        # support both en and fr locales
        kwargs.setdefault('input_formats', ['%d/%m/%Y', '%Y-%m-%d'])
        kwargs.setdefault('help_text', self.DEFAULT_HELP)
        super().__init__(*args, **kwargs)


class DateFieldNative(DateField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', DateInputNative)
        # prevent default help_text from datefield
        kwargs.setdefault('help_text', None)
        super().__init__(*args, **kwargs)
