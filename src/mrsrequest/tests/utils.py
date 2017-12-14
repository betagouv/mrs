import uuid

from django.urls import reverse

from mrsrequest.models import MRSRequest


sessions = [
    {},
    {MRSRequest.SESSION_KEY: {}},
    {MRSRequest.SESSION_KEY: {str(uuid.uuid4()): dict()}},
]


def upload_request(rf, id, file):
    request = rf.post(
        reverse('pmt_upload', args=[id]),
        dict(file=file)
    )
    # Middleware is not called, deal with session manually
    request.session = dict()
    return request
