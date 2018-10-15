import datetime
import pytest

from django.core.exceptions import ValidationError

from mrsrequest.models import MRSRequest
from person.models import Person


def test_person_str():
    p = Person(
        first_name='a',
        last_name='b',
        birth_date='1969-01-01',
    )

    assert str(p) == 'a b 1969-01-01'


@pytest.mark.django_db
def test_person_validate_nir():
    with pytest.raises(ValidationError):
        Person.objects.create(
            first_name='a',
            last_name='b',
            birth_date='1969-01-01',
            nir=123456789012,
            email="foo@foo.fr",
        )


@pytest.mark.django_db
def test_person_get_dates():
    p = Person.objects.create(
        first_name='a',
        last_name='b',
        birth_date='1969-01-01',
        nir=111111111111,
    )

    m0 = MRSRequest.objects.create(
        insured=p,
        status=MRSRequest.STATUS_VALIDATED,
    )
    m0.transport_set.create(
        date_depart='2018-01-01',
        date_return='2018-01-02',
    )

    m1 = MRSRequest.objects.create(
        insured=p,
        status=MRSRequest.STATUS_VALIDATED,
    )
    m1.transport_set.create(
        date_depart='2018-01-01',
        date_return='2018-01-02',
    )

    assert p.get_dates() == {
        'depart': {
            datetime.date(2018, 1, 1): [m1, m0],
        },
        'return': {
            datetime.date(2018, 1, 2): [m1, m0],
        },
    }


@pytest.mark.django_db
def test_person_get_duplicate_dates():
    p = Person.objects.create(
        first_name='a',
        last_name='b',
        birth_date='1969-01-01',
        nir=111111111111,
    )

    m0 = MRSRequest.objects.create(
        insured=p,
        status=MRSRequest.STATUS_VALIDATED,
    )
    m0.transport_set.create(
        date_depart='2018-01-01',
        date_return='2018-01-02',
    )

    m1 = MRSRequest.objects.create(
        insured=p,
        status=MRSRequest.STATUS_VALIDATED,
    )
    m1.transport_set.create(
        date_depart='2018-01-01',
        date_return='2018-01-03',
    )

    assert p.get_duplicate_dates() == {
        'depart': {
            datetime.date(2018, 1, 1): [m1, m0],
        },
    }
