from dbdiff.fixture import Fixture
import pytest

from person.forms import PersonForm
from person.models import Person


@pytest.fixture
def d():
    return dict(
        nir='1234567890123',
        birth_date='1990-01-01',
        first_name='jamesy',
        last_name='lebowski',
        email='example@example.com',
    )


@pytest.fixture
def s():
    return dict(
        nir='1234567890123',
        birth_date='1990-01-01',
        first_name='seb',
        last_name='lebowski',
        email='example@example.com',
    )


# Twins case : two persons linked to the same nir and born at the same date
@pytest.mark.dbdiff(models=[Person])
def test_personform_twins_get_or_create(d, s):
    # We first make a call for jamesy
    form = PersonForm(d)
    form.full_clean()
    result0 = form.get_or_create()

    # Second call should create a new instance,
    # since seb is another person
    form = PersonForm(s)
    form.full_clean()
    result1 = form.get_or_create()
    assert result0 != result1
    Fixture(
        'person/tests/test_personform_twins.json',
        models=[Person]
    ).assertNoDiff()


@pytest.mark.dbdiff(models=[Person])
def test_personform_get_or_create(d):
    form = PersonForm(d)
    form.full_clean()
    result0 = form.get_or_create()

    Fixture(
        './src/person/tests/test_personform.json',
        models=[Person]
    ).assertNoDiff()

    # Second call should not create a new instance
    result1 = form.get_or_create()
    assert result0 == result1
    Fixture(
        'person/tests/test_personform.json',
        models=[Person]
    ).assertNoDiff()

    # different case should also match
    d['first_name'] = d['first_name'].upper()
    d['last_name'] = d['last_name'].upper()
    form = PersonForm(d)
    form.full_clean()
    result2 = form.get_or_create()
    assert result0 == result2

    # email should update though
    d['email'] = 'new@example.com'
    form = PersonForm(d)
    form.full_clean()
    result3 = form.get_or_create()
    assert result0 == result3
    result0.refresh_from_db()
    assert result0.email == 'new@example.com'


def test_personform_clean_nir(d):
    form = PersonForm(d)
    form.full_clean()
    assert 'nir' not in form.errors

    for i in range(0, 12):
        d['nir'] = 'a' * i
        form.full_clean()
        assert 'nir' in form.errors

    d['nir'] = 'aoeu'
    form.full_clean()
    assert 'nir' in form.errors

    d['nir'] = '123456789012a'
    form.full_clean()
    assert 'nir' in form.errors

    d['nir'] = '12345678901234'
    form.full_clean()
    assert 'nir' in form.errors

    d['nir'] = 123456789012
    form.full_clean()
    assert 'nir' in form.errors


def test_personform_clean_birth_date(d):
    form = PersonForm(d)
    form.full_clean()
    assert 'birth_date' not in form.errors

    d['birth_date'] = '2999-01-01'
    form.full_clean()
    assert 'birth_date' in form.errors


@pytest.mark.django_db
def test_personform_clean_last_name(d):
    d['last_name'] = "fooʻʽˈ՚‘ʹ′–−-"
    form = PersonForm(d)
    assert form.is_valid()
    assert form.get_or_create().last_name == "foo'''''''---"


@pytest.mark.django_db
def test_personform_clean_first_name(d):
    d['first_name'] = "fooʻʽˈ՚‘ʹ′–−-"
    form = PersonForm(d)
    assert form.is_valid()
    assert form.get_or_create().first_name == "foo'''''''---"


@pytest.mark.django_db
def test_personform_test_fix_last_name(d):
    p = Person.objects.create(
        first_name='first',
        last_name='last',
        nir=1111111111111,
        birth_date='1990-01-01',
        email='example@example.com',
    )

    # bypass validator to simulate legacy data
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("update person_person set last_name='last!'")

    data = dict(
        nir='1111111111111',
        birth_date='1990-01-01',
        first_name='first',
        last_name='last',
        email='example@example.com',
    )
    form = PersonForm(data)
    assert form.is_valid()
    result = form.get_or_create()
    assert result.pk == p.pk
    assert result.first_name == 'first'
    assert result.last_name == 'last'
