import datetime
import pytest
import pytz
import uuid

from django.utils import timezone
from freezegun import freeze_time

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


@freeze_time('3000-12-31 13:37:42')  # forward compat and bichon <3
@pytest.mark.django_db
def test_display_id():
    assert MRSRequest.objects.create(
        display_id=300012301111,
        creation_datetime=timezone.now() - datetime.timedelta(days=1),
    ).display_id == 300012301111

    assert MRSRequest.objects.create().display_id == '300012310000'
    assert MRSRequest.objects.create().display_id == '300012310001'


@freeze_time('3000-12-31 13:37:42')  # forward compat and bichon <3
def test_mrsrequest_str():
    assert str(MRSRequest(display_id=300012301111)) == '300012301111'


@pytest.mark.django_db
def test_mrsrequest_increments_at_minute_zero():
    paris = pytz.timezone('Europe/Paris')
    paris_yesterday = datetime.datetime(1999, 12, 31, 0, 5, tzinfo=paris)
    assert MRSRequest.objects.create(
        creation_datetime=paris_yesterday).display_id == '199912310000'

    # this is 2000-01-01 in Europe/Paris
    utc_today = datetime.datetime(1999, 12, 31, 23, 5, tzinfo=pytz.utc)

    # do not count the abouve as first
    assert MRSRequest.objects.create(
        creation_datetime=utc_today).display_id == '200001010000'

    paris_today = datetime.datetime(2000, 1, 1, 0, 5, tzinfo=paris)

    # do not count the abouve as first
    assert MRSRequest.objects.create(
        creation_datetime=paris_today).display_id == '200001010001'
