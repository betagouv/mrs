import datetime
import pytest
import pytz
import uuid

from django.utils import timezone
from freezegun import freeze_time

from person.models import Person
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


paris = pytest.fixture(lambda: pytz.timezone('Europe/Paris'))


@pytest.fixture
def paris_yesterday(paris):
    return datetime.datetime(1999, 12, 31, 0, 5, tzinfo=paris)


@pytest.fixture
def utc_today():
    # this is 2000-01-01 in Europe/Paris
    return datetime.datetime(1999, 12, 31, 23, 5, tzinfo=pytz.utc)


@pytest.fixture
def paris_today(paris):
    # objects created with paris_today should be affected by those
    # created with utc_today
    return datetime.datetime(2000, 1, 1, 0, 5, tzinfo=paris)


@pytest.mark.django_db
def test_mrsrequest_increments_at_minute_zero(
        paris, paris_yesterday, paris_today, utc_today):

    assert MRSRequest.objects.create(
        creation_datetime=paris_yesterday
    ).display_id == '199912310000'

    # do not count the abouve as first
    assert MRSRequest.objects.create(
        creation_datetime=utc_today
    ).display_id == '200001010000'

    # do not count the abouve as first
    assert MRSRequest.objects.create(
        creation_datetime=paris_today
    ).display_id == '200001010001'


def test_mrsrequest_day_number_three_digits(paris_yesterday):
    assert MRSRequest(creation_datetime=paris_yesterday).day_number == '365'


def test_mrsrequest_day_number_one_digit(paris_today):
    assert MRSRequest(creation_datetime=paris_today).day_number == '001'


def test_mrsrequest_day_number_timezone_conversion(utc_today):
    assert MRSRequest(creation_datetime=utc_today).day_number == '001'


@pytest.mark.django_db
def test_mrsrequest_order_number(paris_yesterday, paris_today, utc_today):
    person = Person.objects.create(
        first_name='test', last_name='test', nir=1234567890123)

    obj = MRSRequest.objects.create(
        creation_datetime=utc_today, insured=person)
    assert obj.order_number == '01'

    obj = MRSRequest.objects.create(
        creation_datetime=paris_yesterday, insured=person)
    assert obj.order_number == '01'

    # utc_today had impact on number, but not paris_yesterday
    obj = MRSRequest.objects.create(
        creation_datetime=paris_today, insured=person)
    assert obj.order_number == '02'

    for i in range(1, 100):
        # start on 1 to have a different datetime from above
        # not using bulk_create because of the signal
        obj = MRSRequest.objects.create(
            creation_datetime=paris_today + datetime.timedelta(seconds=i),
            insured=person,
        )
        if i >= 98:
            assert obj.order_number == '99'
        else:
            assert obj.order_number == '{:02d}'.format(i + 2), 'object #' + i

    assert obj.order_number == '99'
