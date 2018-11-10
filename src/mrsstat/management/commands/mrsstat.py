from datetime import datetime

from django.core.management.base import BaseCommand

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

    def handle(self, *args, **options):
        if options['refresh']:
            for stat in Stat.objects.all():
                stat.denorm_reset()
                stat.save()

        if options['force']:
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

        if options['date']:
            date = datetime.strptime(options['date'], '%d/%m/%Y').date()
            for stat in Stat.objects.filter(date=date):
                stat.denorm_reset()
                stat.save()
            else:
                Stat.objects.update_date(date)
        else:
            print(f'Creating missing stats now ...')
            Stat.objects.create_missing()
