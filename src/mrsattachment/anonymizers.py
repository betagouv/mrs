from hattori.base import BaseAnonymizer
from mrsattachment.models import MRSAttachment


class MRSAttachmentAnonymizer(BaseAnonymizer):
    model = MRSAttachment

    attributes = [
        ('filename', "1x1.png"),
        ('attachment_file', "1x1.png"),
    ]

    def get_query_set(self):
        return MRSAttachment.objects.all()
