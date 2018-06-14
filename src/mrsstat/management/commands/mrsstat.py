from django.core.management.base import BaseCommand

from mrsstat.models import Stat


class Command(BaseCommand):
    help = 'Create missing Stat models up to yesterday'

    def handle(self, *args, **options):
        Stat.objects.create_missing()
