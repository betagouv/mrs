import io
import multiprocessing

from os.path import splitext

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.management.base import BaseCommand

from mrsrequest.models import PMT, Bill


def save_binary_to_file(id):
    obj = PMT.objects.get(id=id)

    if obj.binary is not None:
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
                print(f'   Error : filename = {filename} -- id = {obj.id}')
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
            print(f'   Error : {e}')

    print(f'{obj} OK !')


class Command(BaseCommand):
    help = 'Save DB file binaries to filesystem'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--type',
            '-t',
            help='Type of attachments to save, "pmt" or "bill" '
                 '-- Default "pmt"'
        )

    def handle(self, *args, **options):
        type = options.get("type") or "pmt"

        # Scan all PMTs / Bills for ones with no 'attachment_file'
        if type == "pmt":
            pmts_ids = PMT.objects\
                .filter(attachment_file__in=['', None])\
                .values_list('id', flat=True)
            with multiprocessing.Pool() as pool:
                pool.map(save_binary_to_file, pmts_ids)
        elif type == "bill":
            bills_ids = Bill.objects\
                .filter(attachment_file__in=['', None])\
                .values_list('id', flat=True)
            with multiprocessing.Pool() as pool:
                pool.map(save_binary_to_file, bills_ids)
        else:
            self.stdout.write(
                self.style.ERROR('Type unknown')
            )

        self.stdout.write(
            self.style.SUCCESS('--- END ---')
        )
