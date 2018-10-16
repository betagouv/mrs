from dbdiff.fixture import Fixture
from django import test
from freezegun import freeze_time

from mrsrequest.models import MRSRequest
from mrsstat.models import update_stat_for_mrsrequest, Stat


class StatTest(test.TransactionTestCase):
    reset_sequences = True
    fixtures = ['src/mrs/tests/data.json']

    @freeze_time('2018-05-06 13:37:42')  # forward compat and bichon <3
    def test_mrsstat(self):
        Stat.objects.create_missing()

        for m in MRSRequest.objects.all():
            update_stat_for_mrsrequest(pk=m.pk)
            m.save()

        Fixture(
            'mrsstat/tests/test_mrsstat.json',
            models=[Stat]
        ).assertNoDiff()
