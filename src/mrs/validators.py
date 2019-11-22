from django.core import validators


name_validators = [
    validators.RegexValidator(
        r'^[\w –−-]+$',
        'Merci de saisir uniquement lettres et tirets',
    ),
    validators.RegexValidator(
        r'^[^\d_]+$',
        'Merci de saisir uniquement lettres et tirets',
    ),
]
