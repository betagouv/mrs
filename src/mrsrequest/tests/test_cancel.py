import os
import pytest
from responsediff.response import Response

from mrsrequest.models import MRSRequest


@pytest.mark.django_db
@pytest.mark.parametrize('name,url,status', [
    ('ok', '{pk}/{token}', 'new'),
    ('ko', '{fakepk}/{faketoken}', 'new'),
    ('ko_canceled', '{pk}/{token}', 'canceled'),
    ('ko_rejected', '{pk}/{token}', 'rejected'),
    ('ko_inprogress', '{pk}/{token}', 'inprogress'),
    ('ko_validated', '{pk}/{token}', 'validated'),
    ('ko_pk', '{fakepk}/{token}', 'new'),
    ('ko_token', '{pk}/{faketoken}', 'new'),
])
def test_mrsrequest_cancel_get(name, url, status, client, mrsrequest_uuid):
    mr = MRSRequest.objects.create(
        token='abc', pk=mrsrequest_uuid,
        status=getattr(MRSRequest, f'STATUS_{status.upper()}')
    )

    resp = client.get('/annuler-demande/' + url.format(
        pk=mr.pk,
        token=mr.token,
        fakepk='a' + str(mr.pk)[:-1],
        faketoken=mr.token[:-1]
    ))

    Response(os.path.join(
        os.path.dirname(__file__),
        'response_fixtures',
        '_'.join(['cancel', name]),
    )).assertNoDiff(resp, '.mrs-std-page--wrapper')
