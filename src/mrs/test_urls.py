import pytest

from django.urls import reverse


@pytest.mark.django_db
def test_index_template(client):
    r = client.get('/')
    assert r.template_name == ['index.html']


def test_demande_reverse():
    assert reverse('demande') == '/demande'


@pytest.mark.django_db
def test_demande_template(client):
    r = client.get('/demande')
    assert r.template_name == ['mrsrequest/form.html']


@pytest.mark.django_db
def test_demande_redirect(client):
    r = client.get('/mrsrequest/wizard/')
    assert r.status_code == 301
    assert r['Location'] == '/demande'
