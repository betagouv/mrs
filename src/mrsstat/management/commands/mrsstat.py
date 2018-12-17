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
        parser.add_argument(
            '--refresh',
            action='store_true',
            dest='refresh',
            help='Only refresh existing stats',
        )

    def refresh(self):
        for req in MRSRequest.objects.all():
            req.denorm_reset()
            req.save()

        for stat in Stat.objects.all():
            stat.denorm_reset()
            stat.save()

    def force(self):
        stats = Stat.objects.all()
        total = stats.count()
        per_percent = total / 100
        percent = 0
        for i, stat in enumerate(stats):
            stat.save()
            percentile = int(i / per_percent)
            if percentile != percent:
                print(f'{percentile}% done refreshing existing')
                percent = percentile

    def date(self, date):
        for stat in Stat.objects.filter(date=date):
            stat.denorm_reset()
            stat.save()
        else:
            Stat.objects.update_date(date)

    def handle(self, *args, **options):
        if options['refresh']:
            return self.refresh()

        if options['force']:
            self.force()

        if options['date']:
            self.date(datetime.strptime(options['date'], '%d/%m/%Y').date())
        else:
            print('Creating missing stats now ...')
            Stat.objects.create_missing()
