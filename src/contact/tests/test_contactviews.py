import pytest

from captcha.models import CaptchaStore
from contact.forms import ContactForm
from mrsrequest.models import MRSRequest


@pytest.fixture
@pytest.mark.django_db
def captcha():
    return CaptchaStore.objects.get_or_create(response='3', hashkey='3')[0]


@pytest.fixture
def data(caisse, captcha):
    return dict(
        motif='request_error',
        caisse=caisse.pk,
        nom='alice',
        email='example@example.com',
        message='J\'écris "salut l\'monde.".',
        mrsrequest_display_id=201801010000,
        captcha_0=captcha.hashkey,
        captcha_1=captcha.response,
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
@pytest.mark.parametrize('motif', ['website_question', 'other'])
def test_contactform_email_kwargs_suggestion(caisse, data, motif):
    data['motif'] = motif
    form = ContactForm(data)
    assert form.is_valid()
    kwargs = form.get_email_kwargs()
    assert caisse.liquidation_email in kwargs['to']


@pytest.mark.django_db
@pytest.mark.parametrize('nom,valid', [
    ('àôéû ôéÉûdhtnùèöâ', True),
    ('àôéû-àôéû', True),
    ('àôéû–àôéû', True),
    ('àôéû−àôéû', True),
    ("aʼʻʽˈ՚‘ʹ′‵Ꞌꞌ'", True),
    ('aoeu<', False),
    ('aoeu>', False),
    ('aoeu"', False),
    ('aoeu\'', True),
    ('aoeu1', False),
    ('aoeu_', False),
    ('aoeu$', False),
])
def test_validation_nom(caisse, data, nom, valid):
    data['nom'] = nom
    form = ContactForm(data)
    assert form.is_valid() == valid
    if not valid:
        assert [*form.errors.keys()] == ['nom']
        assert form.errors['nom'] == [
            'Merci de saisir uniquement lettres et tirets'
        ]


@pytest.mark.django_db
def test_sanitization_nom(caisse, data):
    data['nom'] = "aʼʻʽˈ՚‘ʹ′‵Ꞌꞌ'-−–"
    form = ContactForm(data)
    assert form.is_valid()
    assert form.cleaned_data['nom'] == "a''''''''''''---"


@pytest.mark.django_db
def test_validation_message(caisse, data):
    data['message'] = 'aoeu' * 10000
    form = ContactForm(data)
    assert not form.is_valid()
