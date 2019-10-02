import datetime

from django.core.management.base import BaseCommand

from mrsrequest.models import PMT, Bill


class Command(BaseCommand):
    help = 'Remove MRSAttachment (PMT / Bill) without MRSRequest ' \
           '(aborted / illegal uploads)'

    def handle(self, *args, **options):
        try:
            pmts = PMT.objects.filter(
                pk__in=PMT.objects
                .filter(
                    mrsrequest__isnull=True,
                    creation_datetime__lt=(
                        datetime.datetime.now() - datetime.timedelta(
                            days=8
                        )
                    )
                )
                .values_list('pk', flat=True)
            )
            pmts_count = pmts.count()
            pmts.delete()
            self.stdout.write(
                self.style.SUCCESS('Deleted {} PMTs'.format(pmts_count))
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR('Error : {}'.format(e))
            )

        try:
            bills = Bill.objects.filter(
                pk__in=Bill.objects
                .filter(
                    mrsrequest__isnull=True,
                    creation_datetime__lt=(
                        datetime.datetime.now() - datetime.timedelta(
                            days=8
                        )
                    )
                )
                .values_list('pk', flat=True)
            )
            bills_count = bills.count()
            bills.delete()
            self.stdout.write(
                self.style.SUCCESS('Deleted {} Bills'.format(bills_count))
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR('Error : {}'.format(e))
            )

        self.stdout.write(
            self.style.SUCCESS('--- END ---')
        )
