from decimal import Decimal
import io
import pytest
import os

from crudlfap import crudlfap

from django import test
from django.urls import reverse

from freezegun import freeze_time

from mrsuser.models import User

from responsediff.test import ResponseDiffTestMixin


class ExportTest(ResponseDiffTestMixin, test.TestCase):
    fixtures = ['src/mrs/tests/data.json']

    @freeze_time('3000-12-31 13:37:42')  # forward compat and bichon <3
    def test_export(self):
        fixture_path = os.path.join(os.path.dirname(__file__), 'test_export')
        url = reverse('crudlfap:mrsrequest:export')
        client = test.Client()
        client.force_login(User.objects.get(username='test'))
        response = client.get(url)
        result = str(response.content, 'utf-8')

        if not os.path.exists(fixture_path):
            with open(fixture_path, 'w+') as f:
                f.write(result)
            raise Exception('Fixture created')

        with open(fixture_path, 'r') as f:
            expected = f.read()

        assert expected == result.replace('\r', '')


@pytest.mark.usefixtures('srf_class')
class ImportTest(ResponseDiffTestMixin, test.TransactionTestCase):
    fixtures = ['src/mrs/tests/data.json']
    reset_sequences = True

    upload0 = '''caisse;id;nir;naissance;nom;prenom;transport;mandatement;base;montant;bascule;finess;adeli
bbbb;201805010001;2333333333333;30/04/2000;uea;ue;29/04/2018;;;;;;
bbbb;201805010001;2333333333333;30/04/2000;uea;ée;29/04/2018;10/06/2018;18,32;19;1;310123123;12
aaaaaaa;201805010000;1111111111111;30/04/2000;aoeu;aoeu;29/04/2018;11/06/2018;2;3;0;123123123;
aaaaaaa;999905010000;1111111111111;30/04/2000;aoeu;aoeu;29/04/2018;;;;;;
aaaaaaa;201805010000;1111111111111;30/04/2000;aoeu;aoeu;29/04/2018;30/04/2018;a;3;0;;
    '''.strip()  # noqa

    upload1 = '''caisse;id;nir;naissance;nom;prenom;transport;mandatement;base;montant;bascule;finess;adeli
bbbb;201805010001;2333333333333;30/04/2000;uea;ée;29/04/2018;10/06/2018;18,32;22;1;310123123;12
aaaaaaa;201805010000;1111111111111;30/04/2000;aoeu;aoeu;29/04/2018;11/06/2018;2;3;0;310123122;
aaaaaaa;201805020000;2333333333333;30/04/2000;uea;ée;29/04/2018;10/06/2018;5,32;6;1;310123123;12
    '''.strip()  # noqa

    def upload(self, data):
        fixture = io.BytesIO()
        fixture.write(data.encode('utf-8'))
        fixture.seek(0)

        request = self.srf.post(
            reverse('crudlfap:mrsrequest:import'),
            dict(csv=fixture)
        )
        request.user = User.objects.get(username='test')
        view_class = crudlfap.site['mrsrequest.mrsrequest']['import']
        view = view_class(request=request)
        view.dispatch(request)
        return request, view

    @freeze_time('3000-12-31 13:37:42')  # forward compat and bichon <3
    def test_import(self):
        request, view = self.upload(self.upload0)

        assert view.form.is_valid()
        assert list(view.success.keys()) == [1, 2]
        assert view.errors[3]['message'] == 'FINESS invalide 123123123'  # noqa
        assert view.errors[4]['message'] == 'Demande introuvable en base de données'  # noqa
        assert view.errors[5]['message'] == 'payment_base: La valeur « a » doit être un nombre décimal.'  # noqa

        success = view.success[2]['object']
        assert success.payment_amount == 19
        assert success.payment_base == Decimal('18.32')
        assert success.insured.shifted is True
        assert success.institution.finess == '310123123'
        assert success.adeli == 12
        assert str(success.mandate_date) == '2018-06-10'

        request, view = self.upload(self.upload1)
        assert list(view.success.keys()) == [1, 2, 3]
