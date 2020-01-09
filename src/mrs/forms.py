from django import forms
from django.forms import CharField, EmailField


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


class DateInputNativeWithoutDatepicker(DateInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        super().__init__(*args, **kwargs)


class DateFieldWithoutDatepicker(forms.DateField):
    def __init__(self, *args, **kwargs):
        # support both en and fr locales
        kwargs.setdefault('input_formats', ['%d/%m/%Y', '%Y-%m-%d'])
        super().__init__(*args, **kwargs)


class DateFieldNativeWithoutDatepicker(DateFieldWithoutDatepicker):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', DateInputNativeWithoutDatepicker)
        # prevent default help_text from datefield
        kwargs.setdefault('help_text', None)
        super().__init__(*args, **kwargs)


class TextInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs'].setdefault('placeholder', '')
        super().__init__(*args, **kwargs)


class TextInputNative(TextInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        super().__init__(*args, **kwargs)


class CharFieldNative(CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', TextInputNative)
        super().__init__(*args, **kwargs)


class EmailInput(forms.EmailInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs'].setdefault('placeholder', '')
        super().__init__(*args, **kwargs)


class EmailInputNative(EmailInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        super().__init__(*args, **kwargs)


class EmailFieldNative(EmailField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', EmailInputNative)
        super().__init__(*args, **kwargs)
