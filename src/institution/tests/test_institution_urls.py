import pytest

from django.urls import reverse

from institution.models import Institution


@pytest.mark.django_db
def test_institution_iframe(client):
    i = Institution.objects.create(
        finess=310000000,
        origin='*',
        dynamic_allow=True,
    )
    url = reverse(
        'institution:mrsrequest_iframe',
        args=[i.finess]
    ) + '?origin=' + 'http://localhost'
    r = client.get(url)
    assert r.status_code == 200
