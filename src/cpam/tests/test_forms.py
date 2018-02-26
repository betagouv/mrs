import pytest

from django import forms

from cpam.forms import CPAMChoiceField
from cpam.models import CPAM


@pytest.mark.django_db
def test_cpamchoicefield():
    cpam = CPAM.objects.create(
        code='123123123',
        label='test cpam',
        liquidation_email='liquidation@example.com',
    )
    field = CPAMChoiceField()
    result = field.widget.render('test', cpam.pk)
    assert result == '''<select name="test">
  <option value="">Merci de choisir votre CPAM</option>

  <option value="1">CPAM Haute Garonne</option>

  <option value="2" selected>test cpam</option>

  <option value="other">Autre</option>
</select>'''
