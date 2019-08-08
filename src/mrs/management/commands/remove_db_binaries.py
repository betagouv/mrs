from os.path import splitext

from django.core.management.base import BaseCommand

from mrsrequest.models import PMT, Bill


class Command(BaseCommand):
    help = 'Remove file binaries from DB'

    def remove_binary(self, obj):
        try:
            filename = obj.filename.lower()
            extension = splitext(filename)[-1]

            if extension in ['', '.odt', '.txt', '.docx', '.doc', '.zip',
                             '.tiff', '.bmp']:
                # Keep some binaries depending on extension
                return

            obj.binary = None
            obj.save()

        except Exception as e:
            self.stdout.write(
                self.style.ERROR('   Error : {}'.format(e))
            )

    def handle(self, *args, **options):
        for pmt in PMT.objects.all():
            self.remove_binary(pmt)
        for bill in Bill.objects.all():
            self.remove_binary(bill)

        self.stdout.write(
            self.style.SUCCESS('--- END ---')
        )
