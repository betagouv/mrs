from datetime import datetime

from django.core.management.base import BaseCommand

from mrsrequest.models import MRSRequest
from mrsstat.models import Stat


class Command(BaseCommand):
    help = 'Create missing Stat models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            help='Force update of existing',
        )
        parser.add_argument(
            '--date',
            dest='date',
            help='Deal with specific date dd/mm/yyyy',
        )

    def handle(self, *args, **options):
        if options['force']:
            for m in MRSRequest.objects.filter(insured__shifted=True):
                m.save()

            for stat in Stat.objects.all():
                stat.save()

        if options['date']:
            date = datetime.strptime(options['date'], '%d/%m/%Y').date()
            for stat in Stat.objects.filter(date=date):
                stat.save()
            else:
                Stat.objects.update_date(date)
        else:
            Stat.objects.create_missing()
