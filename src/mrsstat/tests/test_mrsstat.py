import pytest
from dbdiff.fixture import Fixture
from django import test
from freezegun import freeze_time

from mrsrequest.models import MRSRequest
from mrsstat.models import stat_update_person, update_stat_for_mrsrequest, Stat
from person.models import Person


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


@pytest.mark.django_db
def test_stat_update_person_shifted(mocker):
    Fixture('mrs/tests/data.json').load()
    stat_update = mocker.patch('mrsstat.models.stat_update')
    p = Person.objects.exclude(shifted=True).first()
    p.shifted = True
    stat_update_person(Person, instance=p)

    for m in p.mrsrequest_set.all():
        stat_update.assert_called_once_with(type(m), m)
