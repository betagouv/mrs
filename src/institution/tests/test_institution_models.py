import pytest

from django.core.exceptions import ValidationError

from institution.models import Institution


def test_institution_str():
    assert str(Institution(finess=310000000)) == '310000000'


@pytest.mark.django_db
def test_institution_finess():
    Institution(finess=310000000, origin='o').full_clean()

    with pytest.raises(ValidationError):
        Institution(finess=30999999, origin='o').full_clean()
