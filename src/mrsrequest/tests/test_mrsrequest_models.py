from bunch import Bunch
import datetime
from decimal import Decimal
import pytest
import pytz
import uuid

from django.conf import settings
from django.utils import timezone
from freezegun import freeze_time

from mrsuser.models import User
from person.models import Person
from mrsrequest.models import MRSRequest


paris = pytest.fixture(lambda: pytz.timezone('Europe/Paris'))


days = dict(
    yesterday=(1999, 12, 31),
    today=(2000, 1, 1),
    tomorrow=(2000, 1, 2),
)

hours = {'min': (0, 1), 'max': (23, 59)}

tz = dict(
    paris=paris(),
    utc=pytz.utc,
)

dts = Bunch()
for day_name, day_args in days.items():
    for hour_name, hour_args in hours.items():
        for tz_name, tz_arg in tz.items():
            var = f'{day_name}_{hour_name}_{tz_name}'
            dts[var] = tz_arg.localize(datetime.datetime(
                *(day_args + hour_args),
            ))


@pytest.mark.django_db
def test_mrsrequest_update_taxi_cost():
    obj = MRSRequest.objects.create(
        distance=100,
        payment_base=120,
    )
    obj.transport_set.create(
        date_depart='2000-12-12',
        date_return='2000-12-12',
    )
    obj.transport_set.create(
        date_depart='2000-12-10',
        date_return='2000-12-10',
    )
    obj.insured = Person.objects.create(
        first_name='aoeu',
        last_name='aoeu',
        birth_date=datetime.date.today(),
        email='aoeu@aoeu.com',
        nir=1234567890123,
    )
    obj.save()

    assert obj.taxi_cost == Decimal('154.34')
    assert obj.saving == 0

    obj.insured.shifted = True
    obj.save()
    assert obj.saving == Decimal('34.34')


@pytest.mark.django_db
def test_payment_delay():
    obj = MRSRequest.objects.create(
        creation_datetime=datetime.datetime(
            2000, 12, 20, 12, tzinfo=pytz.timezone(settings.TIME_ZONE)
        ),
        mandate_date=datetime.date(2000, 12, 30),
    )
    assert obj.delay == 9.5


@pytest.mark.django_db
def test_update_status_reflection_status_changed(su):

    obj = MRSRequest.objects.create(
        creation_datetime=dts.yesterday_max_paris
    )
    obj.update_status(
        su,
        'validated',
        dts.today_max_paris,
        create_logentry=True
    )
    qs = MRSRequest.objects.all()
    result = qs.status_changed('validated', dts.today_min_paris)
    assert obj in result


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


@freeze_time('3000-12-31 13:37:42')
@pytest.mark.django_db
@pytest.mark.parametrize('dt,expected', [
    ('yesterday_min_paris', False),
    ('yesterday_min_utc', False),
    ('yesterday_max_paris', False),
    ('today_min_paris', True),
    ('yesterday_max_utc', True),
    ('today_min_utc', True),
    ('today_max_paris', True),
    ('today_max_utc', False),
    ('tomorrow_min_paris', False),
    ('tomorrow_min_utc', False),
    ('tomorrow_max_paris', False),
    ('tomorrow_max_utc', False),
])
def test_mrsrequestmanager_status_mrsrequests_status_sideeffect(su, dt,
                                                                expected):

    obj = MRSRequest.objects.create(
        creation_datetime=dts.yesterday_max_utc
    )
    obj.update_status(
        su,
        'validated',
        dts.today_min_paris,
        create_logentry=True
    )
    qs = MRSRequest.objects.all()

    if expected:
        assert obj in list(qs.status_filter('validated', date=dts[dt]))
    else:
        assert obj not in list(qs.status_filter('validated', date=dts[dt]))


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
@pytest.mark.parametrize('dt,expected', [
    ('yesterday_min_paris', '199912310000'),
    ('yesterday_min_utc', '199912310000'),
    ('yesterday_max_paris', '199912310000'),
    ('yesterday_max_utc', '200001010000'),
    ('today_min_paris', '200001010000'),
    ('today_min_utc', '200001010000'),
    ('today_max_paris', '200001010000'),
    ('today_max_utc', '200001020000'),
    ('tomorrow_min_paris', '200001020000'),
    ('tomorrow_min_utc', '200001020000'),
    ('tomorrow_max_paris', '200001020000'),
    ('tomorrow_max_utc', '200001030000'),
])
def test_mrsrequest_increments_at_minute_zero(dt, expected):
    assert MRSRequest.objects.create(
        creation_datetime=dts[dt]
    ).display_id == expected


@pytest.mark.django_db
@pytest.mark.parametrize('dt,expected', [
    ('yesterday_min_paris', '365'),
    ('yesterday_min_utc', '365'),
    ('yesterday_max_paris', '365'),
    ('yesterday_max_utc', '001'),
    ('today_min_paris', '001'),
    ('today_min_utc', '001'),
    ('today_max_paris', '001'),
    ('today_max_utc', '002'),
    ('tomorrow_min_paris', '002'),
    ('tomorrow_min_utc', '002'),
    ('tomorrow_max_paris', '002'),
    ('tomorrow_max_utc', '003'),
])
def test_mrsrequest_inprogress_day_number_three_digits(dt, expected):
    mrsrequest = MRSRequest.objects.create()
    mrsrequest.logentries.create(
        action=MRSRequest.STATUS_INPROGRESS,
        datetime=dts[dt],
        user=User.objects.get_or_create(username='test')[0],
    )
    assert mrsrequest.inprogress_day_number == expected


@pytest.mark.django_db
def test_mrsrequest_order_number():
    person = Person.objects.create(
        first_name='test', last_name='test', nir=1234567890123,
        email="rst@rst.rst", birth_date='1969-01-01',)

    tests = (
        ('yesterday_min_paris', '01'),
        ('yesterday_min_utc', '02'),
        ('yesterday_max_paris', '03'),
        ('today_min_paris', '01'),
        ('yesterday_max_utc', '02'),
        ('today_min_utc', '03'),
        ('today_max_paris', '04'),
        ('tomorrow_min_paris', '01'),
        ('today_max_utc', '02'),
        ('tomorrow_min_utc', '03'),
        ('tomorrow_max_paris', '04'),
        ('tomorrow_max_utc', '01'),
    )

    for dt, expected in tests:
        obj = MRSRequest.objects.create(
            creation_datetime=dts[dt], insured=person)
        assert obj.order_number == expected, f'{dt} {dts[dt]}'


@pytest.mark.django_db
def test_mrsrequest_order_number_sticks_at_99():
    person = Person.objects.create(
        first_name='test', last_name='test', nir=1234567890123,
        email="rst@rst.rst", birth_date='1969-01-01',)

    for i in range(1, 102):
        # start on 1 to have a different datetime from above
        # not using bulk_create because of the signal
        obj = MRSRequest.objects.create(
            creation_datetime=(
                dts.tomorrow_max_utc + datetime.timedelta(seconds=i)
            ),
            insured=person,
        )
        if i >= 100:
            assert obj.order_number == '99'
        else:
            assert obj.order_number == '{:02d}'.format(i), 'object #' + i

    assert obj.order_number == '99'
