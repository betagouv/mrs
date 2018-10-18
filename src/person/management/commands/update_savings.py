from django.core.management.base import BaseCommand
from mrsstat.models import stat_update

from person.models import Person


class Command(BaseCommand):
    help = 'Manually re-calculate savings.'

    def handle(self, *args, **options):
        print("****** Computing savings for all requests of all persons... *****")
        for person in Person.objects.all():
            print("   * updating person {}...".format(person.pk))
            for req in person.mrsrequest_set.all():
                stat_update(type(req), req)

        print("all done.")
