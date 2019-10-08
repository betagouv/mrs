from hattori.base import BaseAnonymizer, faker
from mrsrequest.models import MRSRequest

class MRSRequestAnonymizer(BaseAnonymizer):
    model = MRSRequest

    attributes = [
        ('data', lambda **kwargs: None),
        ('adeli', lambda **kwargs: None),
    ]

    def get_query_set(self):
        return MRSRequest.objects.all()
