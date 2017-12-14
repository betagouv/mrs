import io
import pytest

from freezegun import freeze_time

from django.urls import reverse

from mrsrequest.tests.utils import sessions, upload_request
from pmt.models import PMT


def test_pmt_get_delete_url():
    assert PMT(id=3).get_delete_url() == reverse('pmt_delete', args=[3])


@pytest.mark.django_db  # noqa
@freeze_time('2000-01-02 03:04:05')
def test_pmtmanager_record_upload(rf, mrsrequest):
    '''Test record_upload()'''
    with io.BytesIO(b'lol') as f:
        f.name = 'lol.jpg'
        upload = upload_request(rf, id, f).FILES['file']
        result = PMT.objects.record_upload(mrsrequest, upload)

    assert isinstance(result, PMT)
    assert result.pk
    assert result.mrsrequest.id == mrsrequest.id
    assert result.filename == 'lol.jpg'
    assert result.binary == b'lol'


@pytest.mark.django_db  # noqa
@pytest.mark.parametrize("session", sessions)
def test_pmtmanager_allowed_objects(rf, pmt, session):
    request = rf.get('/')
    request.session = session

    # Test Deny
    assert PMT.objects.allowed_objects(request).count() == 0

    # Allow
    pmt.mrsrequest.allow(request)

    # Test allow
    assert list(PMT.objects.allowed_objects(request)) == [pmt]
