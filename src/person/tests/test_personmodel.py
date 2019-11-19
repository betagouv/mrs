import datetime
import pytest

from django.core.exceptions import ValidationError

from mrsrequest.models import MRSRequest
from person.models import Person, delete_orphan_persons


def test_person_str():
    p = Person(
        first_name='a',
        last_name='b',
        birth_date='1969-01-01',
    )

    assert str(p) == 'a b 1969-01-01'


@pytest.mark.parametrize('nir,expected', [
    (123456789012, 1),
    (12345678901234, 1),
    ('123456A890123', 1),
    ('123456B890123', 1),
    ('123456C890123', 1),
    ('A234566890123', 1),
    ('A23456689012', 2),
    ('A2345668901222', 2),
    (123456789012, 1),
    # Lets support legacy code that treated NIR as int
    (1234567890123, 0),
    ('1234567890123', 0),
    # two acceptable corsican cases with 2 on 6th position
    # and A or B at 7th position
    ('123452A890123', 0),
    ('123452B890123', 0),
    ('123452a890123', 0),
    ('123452b890123', 0),
    (1234567890123, 0),
    (1234567890123, 0),
])
def test_person_validate_nirs(nir, expected):
    person = Person(
        first_name='a',
        last_name='b',
        nir=nir,
        birth_date='1969-01-01',
        email="foo@foo.fr",
    )

    if not expected:
        person.full_clean()
        assert person.nir == str(nir)
    else:
        with pytest.raises(ValidationError) as raised:
            person.full_clean()
        assert len(raised.value.error_dict['nir']) == expected


@pytest.mark.django_db
def test_person_get_dates():
    p = Person.objects.create(
        first_name='a',
        last_name='b',
        birth_date='1969-01-01',
        nir=1234567890123,
        email="foo@foo.fr",
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
        nir=1234567890123,
        email="foo@foo.fr",
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


@pytest.mark.django_db
def test_person_delete_orphans():
    p0 = Person.objects.create(
        first_name='a',
        last_name='b',
        birth_date='1969-01-01',
        nir=1234567890123,
        email="foo@foo.fr",
    )

    MRSRequest.objects.create(
        insured=p0,
        status=MRSRequest.STATUS_VALIDATED,
    )

    Person.objects.create(
        first_name='b',
        last_name='c',
        birth_date='1969-01-01',
        nir=1234567890124,
        email="foo2@foo.fr",
    )

    assert delete_orphan_persons() == 1
