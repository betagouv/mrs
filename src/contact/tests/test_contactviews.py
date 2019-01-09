import pytest

from caisse.models import Caisse
from contact.forms import ContactForm
from contact.views import get_email_data


@pytest.mark.django_db
def test_contactview(p, srf, caisse):
    form_data = dict(
        motif='request_error',
        caisse=caisse.pk,
        nom='alice',
        email='example@example.com',
        message="J'écris \"selfalut l'monde.\".",
    )

    form = ContactForm(form_data)
    assert form.is_valid()
    email_data = get_email_data(form)
    assert email_data['subject'] == 'RÉCLAMATION MRS'
    assert caisse.liquidation_email in email_data['to']
    assert 'Motif: J\'ai fait une erreur' in email_data['body']
