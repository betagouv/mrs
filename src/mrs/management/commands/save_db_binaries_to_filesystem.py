import io

from os.path import splitext

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management.base import BaseCommand

from mrsrequest.models import PMT, Bill


class Command(BaseCommand):
    help = 'Save DB file binaries to filesystem'

    def save_binary_to_file(self, obj):
        if not obj.attachment_file:
            try:
                filename = obj.filename.lower()
                extension = splitext(filename)[-1]
                binary_to_store = obj.binary

                if extension == '.png':
                    mimetype = 'image/png'
                elif extension == '.gif':
                    mimetype = 'image/gif'
                elif extension == '.jpeg' or extension == '.jpg':
                    mimetype = 'image/jpeg'
                elif extension == '.pdf':
                    mimetype = 'application/pdf'
                else:
                    self.stdout.write(
                        self.style.ERROR('   Error : filename = {} -- id = {}'
                                         .format(filename, obj.id))
                    )
                    # Store dummy empty file
                    binary_to_store = b''
                    extension = '.png'
                    mimetype = 'image/png'

                # Stream binary to in-memory Django file
                f = InMemoryUploadedFile(
                    io.BytesIO(binary_to_store),
                    'field_name',
                    'test_file{}'.format(extension),
                    mimetype,
                    len(binary_to_store),
                    None,
                )

                # Save it to the model (which will save it to the filesystem)
                obj.attachment_file = f
                obj.save()

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR('   Error : {}'.format(e))
                )

    def handle(self, *args, **options):
        # Scan all PMTs / Bills for ones with no 'attachment_file'
        for pmt in PMT.objects.filter(attachment_file__isnull=True):
            self.save_binary_to_file(pmt)
        for bill in Bill.objects.filter(attachment_file__isnull=True):
            self.save_binary_to_file(bill)

        self.stdout.write(
            self.style.SUCCESS('--- END ---')
        )
