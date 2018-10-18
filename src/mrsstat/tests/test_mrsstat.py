import pytest
from dbdiff.fixture import Fixture
from django import test
from freezegun import freeze_time

from person.models import Person
from mrsrequest.models import MRSRequest
from mrsstat.models import update_stat_for_mrsrequest, stat_update_person, Stat


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
def test_stat_update_person_shifted(mock):
    Fixture('mrs/tests/data.json').load()
    stat_update_mock = mock.patch('mrsstat.models.stat_update')
    pers = Person.objects.exclude(shifted=True).first()
    pers.shifted = True
    stat_update_person(Person, instance=pers)

    for req in pers.mrsrequest_set.all():
        stat_update_mock.assert_called_once_with(type(req), req)
