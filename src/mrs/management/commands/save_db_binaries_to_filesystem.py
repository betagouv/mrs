import io

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management.base import BaseCommand

from mrsrequest.models import PMT, Bill


class Command(BaseCommand):
    help = 'Save DB file binaries to filesystem'

    def save_binary_to_file(self, obj):
        if not obj.attachment_file:
            self.stdout.write(
                self.style.ERROR('{} has no attachment_file')
                    .format(obj)
            )

            try:
                # Stream binary to in-memory Django file
                f = InMemoryUploadedFile(
                    io.BytesIO(obj.binary),
                    'field_name',
                    'test_file.png',
                    'image/png',
                    len(obj.binary),
                    None,
                )

                # Save it to the model (which will save it to the filesystem)
                obj.attachment_file = f
                obj.save()

                self.stdout.write(
                    self.style.SUCCESS('   OK !')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR('   Error : {}'.format(e))
                )

    def handle(self, *args, **options):
        # Scan all PMTs / Bills for ones with no 'attachment_file'
        for pmt in PMT.objects.all():
            self.save_binary_to_file(pmt)
        for bill in Bill.objects.all():
            self.save_binary_to_file(bill)

        self.stdout.write(
            self.style.SUCCESS('--- END ---')
        )
