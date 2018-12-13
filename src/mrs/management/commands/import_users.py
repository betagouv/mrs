from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from mrsuser.models import User
from caisse.models import Caisse
import csv


def add_user(row):
    agent_nb = row[2]
    username = "{}_{}".format(row[0], agent_nb)
    password = agent_nb

    user, created = User.objects.get_or_create(
        last_name=row[0],
        first_name=row[1],
        email=row[-1],
        username=username,
    )
    if created:
        print("created: {}".format(username))
    else:
        print("already exists: {}".format(username))

    user.password = password
    user.save()

    groups = row[3].split(',')
    user.add_groups(groups)

    caisses_ids = row[4].split(',')
    caisses = []
    for id in caisses_ids:
        try:
            caisses.append(Caisse.objects.get(number=id))
        except ObjectDoesNotExist:
            print("could not find caisse number {}."
                  .format(id))

    if caisses:
        user.caisses.add(*caisses)

    return user


class Command(BaseCommand):
    help = 'Import users and set permissions from csv file.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            dest='file',
            help='csv file',
        )

    def handle(self, *args, **options):
        if not options.get('file'):
            print("usage: mrs import_users -f file.csv")
            exit(1)

        with open(options.get('file'), newline='') as f:
            reader = csv.reader(f, delimiter='\t')  # watch delimiter
            # DictReader ? clunky.
            for row in reader:
                if not row[0]:
                    continue
                elif row[0] == 'NOM' and row[1] == 'PRENOM':
                    continue

                print(row)
                add_user(row)
