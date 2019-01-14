import pytest

from django.conf import settings

from contact.forms import ContactForm


@pytest.fixture
def data(caisse):
    return dict(
        motif='request_error',
        caisse=caisse.pk,
        nom='alice',
        email='example@example.com',
        message='J\'écris "selfalut l\'monde.".',
    )


@pytest.mark.django_db
def test_contactform_email_kwargs_request(p, srf, caisse, data):
    form = ContactForm(data)
    assert form.is_valid()
    kwargs = form.get_email_kwargs()
    assert kwargs['subject'] == 'RÉCLAMATION MRS'
    # do not enable before product team is ready
    assert caisse.liquidation_email in kwargs['to']
    assert 'Motif: J\'ai fait une erreur' in kwargs['body']


@pytest.mark.django_db
def test_contactform_email_kwargs_request_other(p, srf, caisse, data):
    # fixes regression #851
    data['caisse'] = 'other'
    form = ContactForm(data)
    assert form.is_valid()
    kwargs = form.get_email_kwargs()
    assert settings.TEAM_EMAIL in kwargs['to']


@pytest.mark.django_db
@pytest.mark.parametrize('motif', ['website_question', 'other'])
def test_contactform_email_kwargs_suggestion(p, srf, caisse, data, motif):
    data['motif'] = motif
    form = ContactForm(data)
    assert form.is_valid()
    kwargs = form.get_email_kwargs()
    assert settings.TEAM_EMAIL in kwargs['to']
