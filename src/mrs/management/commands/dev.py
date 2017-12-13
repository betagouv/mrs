import os.path

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Migrate/Createsuperuser/Runserver'

    def handle(self, *args, **options):
        call_command('migrate')

        from django.conf import settings
        from django.apps import apps
        user_model = apps.get_model(settings.AUTH_USER_MODEL)
        if not user_model.objects.count():
            call_command('createsuperuser')

        try:
            pid = os.fork()
        except OSError:
            sys.exit(1)

        if pid == 0:
            os.execvp('npm', ['nmp', 'start'])
        else:
            call_command('runserver')
