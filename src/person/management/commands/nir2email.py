from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from person.models import Person


def get_email(nir):
    p = Person.objects.get(nir=nir)
    return p.email

class Command(BaseCommand):
    help = 'Find emails from a list of NIRs.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            dest='file',
            help='file containing space-separated NIRs.',
        )

    def handle(self, *args, **options):
        if options.get('file'):
            emails = []
            no_emails = []
            nir_not_found = []
            multiple_persons = []
            with open(options.get('file'), 'r') as f:
                content = f.read()
            nirs = [it.strip() for it in content.split(' ') if it.strip() != '']

            for nir in nirs:
                if nir.strip():
                    email = None
                    try:
                        email = get_email(nir.strip())
                    except ObjectDoesNotExist:
                        nir_not_found.append(nir.strip())
                    except MultipleObjectsReturned:
                        p = Person.objects.filter(nir=nir.strip()).first()
                        multiple_persons.append("{}: {}".format(nir.strip(), p.email))

                    if email:
                        emails.append(email)
                    else:
                        no_emails.append(nir.strip())

            print("### emails")
            print("\n".join(emails))

            if no_emails:
                print("### L'email des personnes suivantes n'a pas été trouvé:")
                print("\n".join(no_emails))

            if nir_not_found:
                print("### Ces personnes n'ont pas été trouvées:")
                print("\n".join(nir_not_found))

            if multiple_persons:
                print("### Multiples personnes:")
                print("\n".join(multiple_persons))

        else:
            print("usage: mrs nir2email -f file-with-nirs.txt")
            print("The file should have space-separated NIRs.")
