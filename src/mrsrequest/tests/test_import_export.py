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
class ImportTest(ResponseDiffTestMixin, test.TestCase):
    fixtures = ['src/mrs/tests/data.json']

    upload = '''caisse,id,nir,naissance,nom,transport,mandatement,base,montant,bascule,finess,adeli
    bbbb,201805010001,2333333333333,30/04/2018,uea ue,29/04/2018,30/04/2018,18,19,1,310123123,12
    aaaaaaa,201805010000,1111111111111,30/04/2018,aoeu aoeu,29/04/2018,30/04/2018,2,3,0,123123123,
    aaaaaaa,999905010000,1111111111111,30/04/2018,aoeu aoeu,29/04/2018,,,,,,
    '''.strip()  # noqa

    def make_request(self):
        fixture = io.StringIO()
        fixture.write(self.upload)
        fixture.seek(0)

        request = self.srf.post(
            reverse('crudlfap:mrsrequest:import'),
            dict(csv=fixture)
        )
        request.user = User.objects.get(username='test')
        return request

    @freeze_time('3000-12-31 13:37:42')  # forward compat and bichon <3
    def test_import(self):
        request = self.make_request()

        view_class = crudlfap.site['mrsrequest.mrsrequest']['import']
        view = view_class(request=request)
        view.dispatch(request)

        assert view.form.is_valid()
        assert list(view.success.keys()) == [0]
        assert view.errors[1]['message'] == 'FINESS invalide 123123123'  # noqa
        assert view.errors[2]['message'] == 'Demande introuvable en base de données'  # noqa

        success = view.success[0]['object']
        assert success.payment_amount == 19
        assert success.payment_base == 18
        assert success.insured_shift is True
        assert success.institution.finess == '310123123'
        assert str(success.mandate_date) == '2018-04-30'
