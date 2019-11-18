from django.core import validators


name_validators = [
    validators.RegexValidator(
        '^[\w –−-]+$',
        'Merci de saisir uniquement lettres et tirets',
    ),
    validators.RegexValidator(
        '^[^\d_]+$',
        'Merci de saisir uniquement lettres et tirets',
    ),
]
