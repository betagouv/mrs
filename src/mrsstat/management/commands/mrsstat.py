from django.core.management.base import BaseCommand

from mrsstat.models import Stat


class Command(BaseCommand):
    help = 'Create missing Stat models up to yesterday'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            help='Force update of existing',
        )

    def handle(self, *args, **options):
        if options['force']:
            for stat in Stat.objects.all():
                stat.save()
        Stat.objects.create_missing()
