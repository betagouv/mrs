import io
import uuid

from freezegun import freeze_time
import pytest

from mrsrequest.models import MRSRequest
from mrsrequest.tests.utils import upload_request
from pmt.models import PMT
from pmt.views import PMTUploadView


@pytest.mark.django_db
@freeze_time('2000-01-02 03:04:05')
def test_pmtuploadview_create_object(rf, id):
    view = PMTUploadView()
    view.mrsrequest = MRSRequest.objects.create(id=uuid.uuid4())
    with io.BytesIO(b'lol') as f:
        f.name = 'lol.jpg'
        view.upload = upload_request(rf, id, f).FILES['file']
        result = view.create_object()
    assert isinstance(result, PMT)
    assert result.pk
    assert result.mrsrequest.id == view.mrsrequest.id
    assert result.filename == 'lol.jpg'
    assert result.binary == b'lol'
