import io
import pytest
import uuid

from freezegun import freeze_time

from django.urls import reverse

from mrsrequest.models import MRSRequest
from mrsrequest.tests.utils import upload_request
from pmt.models import PMT


def test_pmt_get_delete_url():
    assert PMT(id=3).get_delete_url() == reverse('pmt_delete', args=[3])


@pytest.mark.django_db
@freeze_time('2000-01-02 03:04:05')
def test_pmtmanager_record_upload(rf):
    '''Test record_upload()'''
    mrsrequest = MRSRequest.objects.create(id=uuid.uuid4())
    with io.BytesIO(b'lol') as f:
        f.name = 'lol.jpg'
        upload = upload_request(rf, id, f).FILES['file']
        result = PMT.objects.record_upload(mrsrequest, upload)

    assert isinstance(result, PMT)
    assert result.pk
    assert result.mrsrequest.id == mrsrequest.id
    assert result.filename == 'lol.jpg'
    assert result.binary == b'lol'
