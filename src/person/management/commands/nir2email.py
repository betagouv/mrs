from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from person.models import Person


def get_email(nir):
    p = Person.objects.get(nir=nir)
    return p.email or ""


def parse_nirs(nirs):
    emails = []

    for nir in nirs:
        if nir:
            email = ""

            try:
                email = get_email(nir)

            except ObjectDoesNotExist:
                pass
            except MultipleObjectsReturned:
                p = Person.objects.filter(nir=nir).first()
                email = p.email or ""

            emails.append("{}; {};".format(nir, email))

    return emails


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
            emails = parse_nirs(nirs)

        print("\n".join(emails))
