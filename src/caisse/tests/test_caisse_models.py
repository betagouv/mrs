import pytest

from django.core.exceptions import ValidationError

from caisse.models import Caisse


def test_caisse_model_str():
    assert str(Caisse(name='lol')) == 'lol'


def test_caisse_number_format_rejects_non_numeric():
    with pytest.raises(ValidationError):
        assert Caisse(name='lol', code=1, number='a').full_clean()


def test_caisse_number_format_rejects_negative():
    with pytest.raises(ValidationError):
        assert Caisse(name='lol', code=1, number='-1').full_clean()


def test_caisse_number_format_rejects_above_thousand():
    with pytest.raises(ValidationError):
        assert Caisse(name='lol', code=1, number=1000).full_clean()


@pytest.mark.django_db
def test_caisse_number_format_accepts_number():
    c = Caisse(name='lol', code=1, number='1')
    c.full_clean()
    c.save()
    c.refresh_from_db()
    assert c.number == '001'
