from django.core.management.base import BaseCommand
from person.models import Person
from pprint import pprint


class Command(BaseCommand):
    help = 'Output dates that are in multiple payments for a person'

    def handle(self, *args, **options):
        for p in Person.objects.all():
            dupes = p.get_duplicate_dates()
            if dupes:
                pprint(dupes)
