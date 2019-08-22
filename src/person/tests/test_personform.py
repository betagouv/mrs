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
