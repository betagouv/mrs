import os
import pytest

from freezegun import freeze_time
from responsediff.response import Response

from mrsrequest.models import MRSRequest


mrsrequest_uuid = '2b88b740-3920-44e9-b086-c851f58e7ea7'

scenarios = ('name,url,status', [
    ('ok', '{pk}/{token}', 'new'),
    ('ko', '{fakepk}/{faketoken}', 'new'),
    ('ko_canceled', '{pk}/{token}', 'canceled'),
    ('ko_rejected', '{pk}/{token}', 'rejected'),
    ('ko_inprogress', '{pk}/{token}', 'inprogress'),
    ('ko_validated', '{pk}/{token}', 'validated'),
    ('ko_pk', '{fakepk}/{token}', 'new'),
    ('ko_token', '{pk}/{faketoken}', 'new'),
])


def mrsrequest_factory(status):
    mr = MRSRequest.objects.create(
        token='abc', pk=mrsrequest_uuid, distancevp=42,
        status=getattr(MRSRequest, f'STATUS_{status.upper()}'),
    )

    mr.transport_set.create(
        date_depart='2018-01-01', date_return='2018-01-02')
    mr.transport_set.create(
        date_depart='2018-01-03', date_return='2018-01-04')

    return mr


def cancel_url(mr, url):
    return '/annuler-demande/' + url.format(
        pk=mr.pk,
        token=mr.token,
        fakepk='a' + str(mr.pk)[:-1],
        faketoken=mr.token[:-1]
    )


def scenarize(test):
    return pytest.mark.django_db(
        pytest.mark.parametrize(*scenarios)(
            freeze_time('2018-12-19 13:33:37')(
                test
            )
        )
    )


@scenarize
def test_mrsrequest_cancel_get(name, url, status, client):
    mrsrequest = mrsrequest_factory(status)
    resp = client.get(cancel_url(mrsrequest, url))
    Response(os.path.join(
        os.path.dirname(__file__),
        'response_fixtures',
        '_'.join(['cancel', name]),
    )).assertNoDiff(resp, '.mrs-std-page--wrapper')


@scenarize
def test_mrsrequest_cancel_post(name, url, status, client):
    mrsrequest = mrsrequest_factory(status)
    resp = client.post(cancel_url(mrsrequest, url))
    assert resp.status_code == 200 if name == 'ok' else 500
