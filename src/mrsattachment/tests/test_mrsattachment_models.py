import pytest

from mrsattachment.models import MRSAttachment
from mrsrequest.models import MRSRequest

# TODO : jbm tout revoir

@pytest.mark.django_db
def test_mrsattachmentmanager_upload_records(attachment):
    assert list(MRSAttachment.objects.recorded_uploads(
        attachment.mrsrequest_uuid)) == [attachment]


@pytest.mark.django_db
def test_mrsattachmentmanager_allowed_objects(attachment, srf):
    request = srf.get('/')
    MRSRequest(attachment.mrsrequest_uuid).allow(request)
    assert list(MRSAttachment.objects.allowed_objects(request)) == [attachment]


def test_mrsattachment_tuple():
    assert MRSAttachment(
        filename='a.png',
        binary=b'aoeu',
    ).tuple() == ('a.png', b'aoeu', 'image/png')
