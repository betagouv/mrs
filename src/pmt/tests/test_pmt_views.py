'''
For extra security, integration test with django.

That said we're using view classes which are already unit tested.
'''

import io
import uuid

import pytest

from django import http

from mrsrequest.models import MRSRequest
from mrsrequest.tests.utils import sessions, upload_request
from mrsrequest.views import MRSFileDeleteView, MRSFileUploadView
from pmt.models import PMT


@pytest.fixture
def mrsrequest():
    return MRSRequest.objects.create(id=uuid.uuid4())


@pytest.fixture
def pmt(mrsrequest):
    PMT.objects.all().delete()
    return PMT.objects.create(
        mrsrequest=mrsrequest,
        binary=b'lol',
        filename='lol.jpg',
    )


@pytest.mark.django_db
@pytest.mark.parametrize("session", sessions)
def test_pmtdeleteview_security_allow(rf, mrsrequest, pmt, session):
    '''Should let me delete PMT of my MRSRequest.'''
    delete_view = MRSFileDeleteView.as_view(model=PMT)
    delete_request = rf.delete(pmt.get_delete_url())
    delete_request.session = session

    # Test Deny
    with pytest.raises(http.Http404):
        delete_view(delete_request, pk=pmt.pk)
    assert PMT.objects.filter(pk=pmt.pk).count() == 1, (
        'should not have been deleted')

    # Allow
    mrsrequest.allow(delete_request)

    # Test allow
    response = delete_view(delete_request, pk=pmt.pk)
    assert response.status_code == 200, 'should return 200'
    assert PMT.objects.filter(pk=pmt.pk).count() == 0, (
        'should have been deleted')


@pytest.mark.django_db
@pytest.mark.parametrize("session", sessions)
def test_pmtuploadview_security(rf, mrsrequest, session):
    '''Should let me upload PMT if to my MRSRequest otherwise update.'''

    upload_view = MRSFileUploadView.as_view(model=PMT)

    with io.BytesIO(b'lol') as f:
        f.name = '1.png'
        request = upload_request(rf, mrsrequest.id, f)
        request.session = session

        # Test deny
        response = upload_view(request, mrsrequest_uuid=mrsrequest.id)
        assert response.status_code == 400, 'Should return 400 before allow'
        assert PMT.objects.count() == 0, 'Should not have created any PMT'

        # Allow
        mrsrequest.allow(request)

        # Test allow
        response = upload_view(request, mrsrequest_uuid=mrsrequest.id)
        assert response.status_code == 201, 'should return 201'
        assert PMT.objects.count() == 1, 'should have been created'
        assert PMT.objects.first().filename == '1.png', (
            'should have been updated')

        # Test update
        f.name = '2.png'
        request = upload_request(rf, mrsrequest.id, f)
        mrsrequest.allow(request)
        response = upload_view(request, mrsrequest_uuid=mrsrequest.id)
        assert PMT.objects.first().filename == '2.png', (
            'should have been updated')
        assert PMT.objects.count() == 1, 'should have been updated'
        assert response.status_code == 201, 'should return 201'
