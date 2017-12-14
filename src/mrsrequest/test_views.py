from dbdiff.fixture import Fixture
import pytest

from django.urls import reverse

from person.models import Person
from pmt.models import PMT
from mrsrequest.models import MRSRequest
from transport.models import Transport, Bill


def form_data():
    return dict(
        transported_first_name='First',
        transported_last_name='Last',
        transported_birth_date='2000-01-01',
    )


@pytest.mark.django_db
def test_your_import(client):
    response = client.post(
        reverse('mrsrequest_create'),
    )
    assert response.status_code == 200

    Fixture(
        './tests/first.json',
        models=[MRSRequest, Person, PMT, Transport, Bill]
    ).assertNoDiff()
