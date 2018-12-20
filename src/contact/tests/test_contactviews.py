import pytest

from caisse.models import Caisse
from contact.forms import ContactForm
from contact.views import get_email_data


@pytest.mark.django_db
def test_contactview(p, srf):
    Caisse.objects.create(
        code="999",
        name="caisse",
        number="001",
        liquidation_email="caisse@example.com",
        active=True,
    )

    form_data = dict(
        motif='request_error',
        caisse=1,
        nom='alice',
        email='example@example.com',
        message="J'écris \"selfalut l'monde.\".",
    )

    def d():
        return form_data

    form = ContactForm(d())
    assert form.is_valid()
    email_data = get_email_data(form)
    assert email_data['subject'] == 'RÉCLAMATION MRS'
    assert 'caisse@example.com' in email_data['to']
    assert 'Motif: Erreur dans votre demande' in email_data['body']
