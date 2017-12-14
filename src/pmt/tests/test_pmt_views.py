import io

from dbdiff.fixture import Fixture
from freezegun import freeze_time
import pytest

from django.urls import reverse

from mrsrequest.models import MRSRequest
from pmt.models import PMT
from pmt.views import PMTUploadView


id = pytest.fixture(lambda: '2b88b740-3920-44e9-b086-c851f58e7ea7')


def upload_request(rf, id, file):
    request = rf.post(
        reverse('pmt_upload', args=[id]),
        dict(file=file)
    )
    # Middleware is not called, deal with session manually
    request.session = dict()
    return request


@pytest.mark.django_db
@freeze_time('2000-01-02 03:04:05')
def test_pmt_upload_on_allowed_id(rf, id):
    with io.BytesIO(b'lol') as f:
        request = upload_request(rf, id, f)
        MRSRequest(id=id).allow(request)
        PMTUploadView().dispatch(request, mrsrequest_uuid=id)

    Fixture(
        './src/pmt/tests/test_pmt_views.test_pmt_upload_on_allowed_id.json',
        models=[MRSRequest, PMT]
    ).assertNoDiff()


@pytest.mark.django_db
def test_pmt_upload_on_not_allowed_id(rf, id):
    with io.BytesIO(b'lol') as f:
        request = upload_request(rf, id, f)
        response = PMTUploadView().dispatch(request, mrsrequest_uuid=id)
    assert response.status_code == 400
