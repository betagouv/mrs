import pytest
from dbdiff.fixture import Fixture
from django import test
from freezegun import freeze_time

from person.models import Person
from mrsrequest.models import MRSRequest
from mrsstat.models import (
    increment,
    update_stat_for_mrsrequest,
    stat_update_person,
    Stat,
)


class StatTest(test.TransactionTestCase):
    reset_sequences = True
    fixtures = ['src/mrs/tests/data.json']

    @freeze_time('2018-05-06 13:37:42')
    def test_mrsstat(self):
        Stat.objects.create_missing()

        for m in MRSRequest.objects.all():
            update_stat_for_mrsrequest(pk=m.pk)
            m.save()

        Fixture(
            'mrsstat/tests/test_mrsstat.json',
            models=[Stat]
        ).assertNoDiff()


@freeze_time('2018-05-06 13:37:42')
@pytest.mark.django_db
def test_stat_update():
    Fixture('mrs/tests/data.json').load()
    req = MRSRequest.objects.get(display_id=201805020002)
    assert req, 'MRSRequest with saving required for this test !'
    MRSRequest.objects.filter(pk=req.pk).update(saving=None)
    req.refresh_from_db()
    assert req.saving is None

    stat_update_person(Person, instance=req.insured)
    req.refresh_from_db()
    assert f'{req.saving}' == '8.83'

    stats = Stat.objects.filter(
        date=req.status_datetime.date(),
        caisse__in=(req.caisse, None),
    )
    for stat in stats:
        assert str(stat.savings) == '8.83'

    req.distancevp *= 2
    req.save()
    req.refresh_from_db()
    assert f'{req.saving}' == '16.20'

    # test that it refreshed stats !
    update_stat_for_mrsrequest(pk=req.pk)

    stats = Stat.objects.filter(
        date=req.status_datetime.date(),
        caisse__in=(req.caisse, None),
    )
    for stat in stats:
        assert str(stat.savings) == '16.20'


@freeze_time('2018-05-06 13:37:42')
@pytest.mark.django_db
def test_stat_increment():
    Stat.objects.filter(date='2018-05-06').delete()
    increment(name='mrsrequest_count_conflicted', count=1)
    assert Stat.objects.get(date='2018-05-06').mrsrequest_count_conflicted == 1
    increment(name='mrsrequest_count_conflicted', count=2)
    assert Stat.objects.get(date='2018-05-06').mrsrequest_count_conflicted == 3
