import pytest
from freezegun import freeze_time

from dbdiff.fixture import Fixture
from django.core.exceptions import ValidationError

from caisse.models import monthly_mail, Caisse


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


@freeze_time('2018-06-01T17:09:27Z')
@pytest.mark.django_db
def test_monthly_mail(mailoutbox, django_assert_num_queries):
    Fixture('./src/mrs/tests/data.json').load()
    with django_assert_num_queries(5):
        monthly_mail()

    assert mailoutbox[0].attachments[0][0] == '2018-6-stats.csv'
    assert mailoutbox[0].attachments[0][1] == 'caisse;id;nir;naissance;transport;mandatement;base;montant;bascule;finess;adeli\n111;201805020000;3212312312312;06/05/2000;26/03/2018;;;;;;'  # noqa
    assert mailoutbox[0].attachments[0][2] == 'text/csv'

    assert mailoutbox[1].attachments[0][0] == '2018-6-stats.csv'
    assert mailoutbox[1].attachments[0][1] == 'caisse;id;nir;naissance;transport;mandatement;base;montant;bascule;finess;adeli\n222;201805010001;2333333333333;30/04/2000;29/04/2018;;;;;;\n222;201805030000;1223123123123;29/05/2000;01/05/2018;;;;;;\n222;201805030001;1223123123123;29/05/2000;01/04/2018;;;;;;'  # noqa
    assert mailoutbox[1].attachments[0][2] == 'text/csv'
