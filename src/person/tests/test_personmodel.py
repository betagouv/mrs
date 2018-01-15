from person.models import Person


def test_person_str():
    p = Person(
        first_name='a',
        last_name='b',
        birth_date='1969-01-01',
    )

    assert str(p) == 'a b 1969-01-01'
