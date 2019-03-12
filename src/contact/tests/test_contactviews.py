import bunch
import pytest

from django.conf import settings

from mrsrequest.models import MRSRequest
from contact.forms import ContactForm
from contact import captcha


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.setattr(
        captcha,
        'get_current_request',
        lambda: bunch.Bunch(session=bunch.Bunch(captcha=[1, 2]))
    )


@pytest.fixture
def data(caisse):
    return dict(
        motif='request_error',
        caisse=caisse.pk,
        nom='alice',
        email='example@example.com',
        message='J\'écris "salut l\'monde.".',
        mrsrequest_display_id='201801010000',
        captcha=3,
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

    # test the form save method
    obj = form.save()
    assert obj.caisse == caisse
    assert obj.email == data['email']
    assert obj.name == data['nom']
    assert obj.message == data['message']
    assert obj.mrsrequest is None

    # check that it attaches the request if it exists
    mrs = MRSRequest.objects.create(display_id=data['mrsrequest_display_id'])
    assert form.save().mrsrequest == mrs


@pytest.mark.django_db
def test_contactform_email_kwargs_request_other(p, srf, caisse, data):
    # fixes regression #851
    data['caisse'] = 'other'
    form = ContactForm(data)
    assert form.is_valid()
    kwargs = form.get_email_kwargs()
    assert settings.TEAM_EMAIL in kwargs['to']
    obj = form.save()
    assert obj.caisse is None


@pytest.mark.django_db
@pytest.mark.parametrize('motif', ['website_question', 'other'])
def test_contactform_email_kwargs_suggestion(p, srf, caisse, data, motif):
    data['motif'] = motif
    form = ContactForm(data)
    assert form.is_valid()
    kwargs = form.get_email_kwargs()
    assert settings.TEAM_EMAIL in kwargs['to']
