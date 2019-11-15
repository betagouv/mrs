from django.core.management.base import BaseCommand

from mrsrequest.models import MRSRequest
from person.models import Person


class Command(BaseCommand):
    help = 'Remove Person duplicates from MRS'

    def handle(self, *args, **options):

        persons = dict()
        mrsrequests_updated = 0
        persons_deleted = 0

        # Identify all Person duplicates in a list
        for p in Person.objects.all():
            key = f'{p.first_name.lower()}{p.nir}{p.birth_date}'
            persons.setdefault(key, [])
            persons[key].append(p.id)

        duplicates = [v for v in persons.values() if len(v) > 1]

        # For every Person's duplicates
        for d in duplicates:
            # Store the most recent one
            max_id = max(d)

            # Store the other duplicates
            ids_to_delete = [x for x in d if x != max_id]

            try:
                # Update the associated MRSRequest with the most recent
                # duplicate among duplicates for this person
                mrsrequests_updated += MRSRequest.objects.filter(
                    insured_id__in=ids_to_delete).update(insured=max_id)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        'Error while updating MRSRequests attached to Persons '
                        'with ids N°{}'.format(str(ids_to_delete)[1:-1]))
                )
                self.stdout.write(
                    self.style.ERROR('Error details : {}'.format(e))
                )

            try:

                # Delete the oldest duplicates among duplicates for this person
                persons_deleted += Person.objects.filter(
                    id__in=ids_to_delete).delete()[0]

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        'Error while deleting Persons with ids N°{}'.format(
                            str(ids_to_delete)[1:-1]))
                )
                self.stdout.write(
                    self.style.ERROR('Error details : {}'.format(e))
                )

        self.stdout.write(
            self.style.SUCCESS(
                'Updated {} MRSRequests'.format(mrsrequests_updated))
        )

        self.stdout.write(
            self.style.SUCCESS(
                'Deleted {} Persons'.format(persons_deleted))
        )

        self.stdout.write(
            self.style.SUCCESS('--- END ---')
        )
