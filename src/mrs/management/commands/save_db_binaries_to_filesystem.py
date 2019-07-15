import io

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management.base import BaseCommand

from mrsrequest.models import MRSRequest


class Command(BaseCommand):
    help = 'Save DB file binaries to filesystem'

    def handle(self, *args, **options):
        for mrsrequest in MRSRequest.objects.all():
            for pmt in mrsrequest.pmt_set.all():
                if not pmt.attachment_file:
                    self.stdout.write(
                        self.style.ERROR('{} has no attachment_file')
                            .format(pmt)
                    )

                    try:
                        f = InMemoryUploadedFile(
                            io.BytesIO(pmt.binary),
                            'field_name',
                            'test_file.png',
                            'image/png',
                            len(pmt.binary),
                            None,
                        )

                        pmt.attachment_file = f
                        pmt.save()

                        self.stdout.write(
                            self.style.SUCCESS('   OK !')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR('   Error : {}'.format(e))
                        )
