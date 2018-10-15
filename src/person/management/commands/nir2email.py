from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from person.models import Person


def get_email(nir):
    p = Person.objects.get(nir=nir)
    return p.email


def parse_nirs(nirs):
    emails = []
    no_emails = []
    nir_not_found = []
    multiple_persons = []

    for nir in nirs:
        if nir:
            email = None

            try:
                email = get_email(nir)
                if email:
                    emails.append(email)
                else:
                    no_emails.append(nir)

            except ObjectDoesNotExist:
                nir_not_found.append(nir)
            except MultipleObjectsReturned:
                p = Person.objects.filter(nir=nir).first()
                multiple_persons.append("{}: {}".format(
                    nir.strip(), p.email))

    return emails, no_emails, nir_not_found, multiple_persons


class Command(BaseCommand):
    help = 'Find emails from a list of NIRs.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            dest='file',
            help='file containing NIRs, one per line.',
        )

    def handle(self, *args, **options):
        if not options.get('file'):
            print("usage: mrs nir2email -f file-with-nirs.txt")
            print("The file should have a NIR per line.")
            return

        if options.get('file'):
            with open(options.get('file'), 'r') as f:
                nirs = f.readlines()

            nirs = [it.strip() for it in nirs]
            emails, no_emails, nir_not_found, multiple_persons = parse_nirs(nirs)  # noqa

            print("### emails")
            print("\n".join(emails))

            if no_emails:
                print("### L'email des personnes suivantes n'a pas été trouvé:")  # noqa
                print("\n".join(no_emails))

            if nir_not_found:
                print("### Ces personnes n'ont pas été trouvées:")
                print("\n".join(nir_not_found))

            if multiple_persons:
                print("### Multiples personnes:")
                print("\n".join(multiple_persons))
