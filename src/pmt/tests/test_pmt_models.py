import io
import pytest

from freezegun import freeze_time

from django.urls import reverse

from mrsattachment.tests.utils import upload_request
from pmt.models import PMT


def test_pmt_get_delete_url():
    assert PMT(id=3).get_delete_url() == reverse('pmt:pmt_destroy', args=[3])


@pytest.mark.django_db  # noqa
@freeze_time('2000-01-02 03:04:05')
def test_pmtmanager_record_upload(rf, mrsrequest):
    '''Test record_upload()'''
    with io.BytesIO(b'lol') as f:
        upload = upload_request(rf, id, f).FILES['file']
        result = PMT.objects.record_upload(mrsrequest, upload)

    assert isinstance(result, PMT)
    assert result.pk
    assert result.mrsrequest.id == mrsrequest.id
    assert result.filename == '1.png'
    assert result.binary == b'lol'


@pytest.mark.django_db  # noqa
def test_pmtmanager_allowed_objects(srf, pmt):
    request = srf.get('/')

    # Test Deny
    assert PMT.objects.allowed_objects(request).count() == 0

    # Allow
    pmt.mrsrequest.allow(request)

    # Test allow
    assert list(PMT.objects.allowed_objects(request)) == [pmt]
