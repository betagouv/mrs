from django.core.management.base import BaseCommand

from person.models import Person


class Command(BaseCommand):
    help = 'Find dates that are in multiple requests for a user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nir',
            dest='nir',
            help='Use against a specific NIR',
        )

    def handle(self, *args, **options):
        if options.get('nir'):
            p = Person.objects.get(nir=options['nir'])
            print(p.get_duplicate_dates())
        else:
            for p in Person.objects.all():
                res = p.get_duplicate_dates()
                if res:
                    for i, dates in res.items():
                        for date, mrsrequests in dates.items():
                            nums = ' '.join(
                                [str(m.display_id) for m in mrsrequests]
                            )
                            print(f'{p.nir} {i} {date}: {nums}')
