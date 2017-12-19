'''
For extra security, integration test with django.

That said we're using view classes which are already unit tested.
'''

import io

import pytest

from django import http

from mrsattachment.tests.utils import upload_request
from mrsattachment.views import MRSFileDeleteView, MRSFileUploadView
from transport.models import Bill


@pytest.mark.django_db
def test_billdeleteview_security_allow(srf, mrsrequest, bill):
    '''Should let me delete Bills of my MRSRequest.'''
    view = MRSFileDeleteView.as_view(model=Bill)
    request = srf.delete(bill.get_delete_url())

    # Test Deny
    with pytest.raises(http.Http404):
        view(request, pk=bill.pk)
    assert Bill.objects.filter(pk=bill.pk).count() == 1, (
        'should not have been deleted')

    # Allow
    mrsrequest.allow(request)

    # Test allow
    response = view(request, pk=bill.pk)
    assert response.status_code == 200, 'should return 200'
    assert Bill.objects.filter(pk=bill.pk).count() == 0, (
        'should have been deleted')


@pytest.mark.django_db
def test_billuploadview_security(srf, mrsrequest):
    '''Should let me upload Bill on my MRSRequest otherwise update.'''

    upload_view = MRSFileUploadView.as_view(model=Bill)

    with io.BytesIO(b'lol') as f:
        request = upload_request(srf, mrsrequest.id, f)

        # Test deny
        response = upload_view(request, mrsrequest_uuid=mrsrequest.id)
        assert response.status_code == 400, 'Should return 400 before allow'
        assert Bill.objects.count() == 0, 'Should not have created any Bill'

        # Allow
        mrsrequest.allow(request)

        # Test allow
        response = upload_view(request, mrsrequest_uuid=mrsrequest.id)
        assert response.status_code == 201, 'should return 201'
        assert Bill.objects.count() == 1, 'should have been created'
        assert Bill.objects.first().filename == '1.png', (
            'should have been updated')

        # Test update
        request = upload_request(srf, mrsrequest.id, f, name='2.png')
        mrsrequest.allow(request)
        response = upload_view(request, mrsrequest_uuid=mrsrequest.id)
        assert Bill.objects.first().filename == '2.png', (
            'should have been updated')
        assert Bill.objects.count() == 1, 'should have been updated'
        assert response.status_code == 201, 'should return 201'
