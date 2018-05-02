import pytest


@pytest.mark.django_db
def test_demande_redirect(client):
    r = client.get('/mrsrequest/wizard/')
    assert r.status_code == 301
    assert r['Location'] == '/demande'


@pytest.mark.django_db
def test_stats(client):
    r = client.get('/stats/')
    assert r.status_code == 301
    assert r['Location'] == '/stats'
