import pytest
import uuid

from mrsrequest.models import MRSRequest


def test_mrsrequest_allow(srf):
    '''allow(request) should be required to pass is_allowed(request)'''
    request = srf.get('/')

    # is_allowed() should fail in a bunch of cases
    mrsrequest = MRSRequest(id=uuid.uuid4())
    assert not mrsrequest.is_allowed(request)

    request.session[MRSRequest.SESSION_KEY] = dict()
    assert not mrsrequest.is_allowed(request)

    request.session[MRSRequest.SESSION_KEY][str(uuid.uuid4())] = dict()
    assert not mrsrequest.is_allowed(request)

    # allow() should change result of is_allowed()
    mrsrequest.allow(request)
    assert mrsrequest.is_allowed(request)


@pytest.mark.django_db
def test_mrsrequestmanager_allowed_objects(srf):
    '''Request should not be able to access MRSRequest prior to allow().'''
    request = srf.get('/')
    mrsrequest = MRSRequest.objects.create()

    # Test deny
    assert mrsrequest not in MRSRequest.objects.allowed_objects(request)

    # Allow request
    mrsrequest.allow(request)

    # Test allow
    assert mrsrequest in MRSRequest.objects.allowed_objects(request)
