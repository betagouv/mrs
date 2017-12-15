import os
import os.path
import secrets
import string
import subprocess
import sys

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.commands.runserver import Command
from django.core.management.base import BaseCommand


def rnpw(num=18):
    return ''.join(secrets.choice(
        string.ascii_uppercase + string.digits) for _ in range(num))


class Command(Command):
    help = 'Migrate/Createsuperuser/Runserver&NPMWatch'

    def handle(self, *args, **options):
        call_command('migrate')
        self.createsuperuser()
        self.runserver(*args, **options)

    def runserver(self, *args, **options):
        try:
            pid = os.fork()
        except OSError:
            sys.exit(1)

        if pid == 0:
            self.webpackwatch()
        else:
            return super().handle(*args, **options)

    def webpackwatch(self):
        watch = '.npm-watch.pid'

        if os.path.exists(watch):
            with open(watch, 'r') as f:
                pid = f.read().strip()

            if pid:
                pid = int(pid)
                if os.path.exists('/proc/{}'.format(pid)):
                    os.kill(pid, 9)

            os.unlink(watch)

        process = subprocess.Popen(
            ['npm start -- --watch'],
            shell=True,
        )
        with open(watch, 'w+') as f:
            f.write(str(process.pid))

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
