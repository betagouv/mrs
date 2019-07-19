from hattori.base import BaseAnonymizer, faker
from mrsattachment.models import MRSAttachment

class MRSAttachmentAnonymizer(BaseAnonymizer):
    model = MRSAttachment

    attributes = [
        ('filename', "fake.png"),
        # TODO : jbm tester une fois jbm-files-out-of-db mergée
        # ('attachment_file', "fake.png"),
    ]

    def get_query_set(self):
        return MRSAttachment.objects.all()
