import pytest

from django.urls import reverse


@pytest.mark.django_db
def test_transport_create(client):
    response = client.get(reverse('transport_create'))
    assert response.status_code == 200
