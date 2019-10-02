import pytest

from mrsattachment.models import MRSAttachment
from mrsrequest.models import MRSRequest


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
        attachment_file='d359fdfb-779b-40e0-b5cc-3829c4e8ef33-791b8911-3454-486d-88d5-9843ccd30143.png'  # noqa
    ).tuple() == (
        'a.png',
        'd359fdfb-779b-40e0-b5cc-3829c4e8ef33-791b8911-3454-486d-88d5-9843ccd30143.png',  # noqa
        'image/png'
    )
