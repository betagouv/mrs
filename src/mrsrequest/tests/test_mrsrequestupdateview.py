from django import test
from django.test.client import Client
from dbdiff.fixture import Fixture

from mrsrequest.models import MRSRequest


class MRSRequestUpdateTestCase(test.TransactionTestCase):
    def test_updateview(self):
        Fixture('./src/mrs/tests/data.json').load()
        mrsrequest = MRSRequest.objects.filter(status=1).first()
        url = mrsrequest.get_update_url()
        cl = Client()
        cl.get(url)
        import ipdb; ipdb.set_trace()
