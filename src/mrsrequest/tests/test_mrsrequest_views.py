import io

from dbdiff.fixture import Fixture
from freezegun import freeze_time
import mock
import pytest

from django.views import generic
from django.urls import reverse

from person.models import Person
from pmt.models import PMT
from mrsrequest.models import MRSRequest
from mrsrequest.tests.utils import upload_request
from mrsrequest.views import MRSFileUploadMixin
from transport.models import Transport, Bill


class FileUploadView(MRSFileUploadMixin, generic.View):
    create_object_return_value = mock.Mock()

    def create_object(self):
        self.create_object_return_value.mrsrequest = self.mrsrequest
        self.create_object_return_value.upload = self.upload
        self.create_object_return_value.get_delete_url.return_value = '/del'
        return self.create_object_return_value


@pytest.mark.django_db
def test_mrsfileuploadmixin_upload_on_not_allowed_id(rf, id):
    with io.BytesIO(b'lol') as f:
        request = upload_request(rf, id, f)
        response = FileUploadView().dispatch(request, mrsrequest_uuid=id)
    assert response.status_code == 400


@pytest.mark.django_db
@freeze_time('2000-01-02 03:04:05')
def test_mrsfileuploadmixin_create_object_call(rf, id):
    view = FileUploadView()
    with io.BytesIO(b'lol') as f:
        request = upload_request(rf, id, f)
        MRSRequest(id=id).allow(request)
        response = view.dispatch(request, mrsrequest_uuid=id)
    assert response.status_code == 201
    assert view.mrsrequest.id == id
    assert view.object == view.create_object_return_value, (
        'should be the retval of create_object()')
    assert view.object.mrsrequest == view.mrsrequest
    assert view.object.upload == view.upload


def form_data():
    return dict(
        transported_first_name='First',
        transported_last_name='Last',
        transported_birth_date='2000-01-01',
    )


@pytest.mark.django_db
def test_your_import(client):
    pytest.skip()
    client.post(
        reverse('mrsrequest_create'),
        form_data()
    )

    Fixture(
        './tests/first.json',
        models=[MRSRequest, Person, PMT, Transport, Bill]
    ).assertNoDiff()
