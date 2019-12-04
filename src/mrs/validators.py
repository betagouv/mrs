from django.core import validators


name_validators = [
    validators.RegexValidator(
        r"^[\w ’ʼʻʽˈ՚‘ʹ′‵Ꞌꞌ'–−-]+$",
        'Merci de saisir uniquement lettres et tirets',
    ),
    validators.RegexValidator(
        r'^[^\d_]+$',
        'Merci de saisir uniquement lettres et tirets',
    ),
]


def name_clean(name):
    replaces = {
        "'": "’ʼʻʽˈ՚‘ʹ′‵Ꞌꞌ'",
        "-": "–−-",
    }
    for clean, dirties in replaces.items():
        for dirty in dirties:
            name = name.replace(dirty, clean)
    return name
