import os
import os.path
import secrets
import string
import subprocess
import sys

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


def rnpw(num=18):
    return ''.join(secrets.choice(
        string.ascii_uppercase + string.digits) for _ in range(num))


class Command(BaseCommand):
    help = 'Migrate/Createsuperuser/Runserver&NPMWatch'

    def handle(self, *args, **options):
        call_command('migrate')
        self.createsuperuser()
        self.runserver()

    def runserver(self):
        try:
            pid = os.fork()
        except OSError:
            sys.exit(1)

        if pid == 0:
            try:
                print('Search npm process, if found, will print the id')
                subprocess.check_call(['pgrep', '-f', 'npm'])
            except subprocess.CalledProcessError:
                print('npm process not found, executing npm start')
                os.execvp('npm', ['npm', 'start'])
        else:
            call_command('runserver')

    def createsuperuser(self):
        user_model = apps.get_model(settings.AUTH_USER_MODEL)
        if not user_model.objects.count():
            admin = user_model.objects.create(
                username=os.getenv('USER', 'admin' + rnpw(3)),
                email='{}@localhost'.format(os.getenv('USER', 'example')),
            )

            password = rnpw()
            admin.set_password(password)
            admin.save()
            print('Login with {} / {}'.format(admin.username, password))
