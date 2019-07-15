import pytest

from dbdiff.fixture import Fixture
from django.test import Client

from mrsuser.models import User
from mrsrequest.models import MRSRequest, PMT


@pytest.mark.django_db
@pytest.mark.parametrize('groups', [
    ['stat', 'support'],
    ['superviseur'],
    ['support'],
    ['upn', 'support'],
    ['upn'],
    ['stat', 'upn'],
])
def test_mrsfiledownloadview_admins(groups, request_factory, caisse, upload):
    Fixture('./src/mrs/tests/data.json').load()

    mrsrequest = MRSRequest(caisse=caisse)
    mrsrequest.pmt = PMT.objects.create(
        mrsrequest_uuid=mrsrequest.id,
        filename='test_mrsrequestcreateview_story.jpg',
        attachment_file=upload
    )
    mrsrequest.save()
    mrsrequest.save_pmt()

    user = User(username='test_mrsfileuploadview_admins')
    user.set_password('secret')
    user.save()
    user.add_groups(groups)
    user.caisses.add(caisse)

    client = Client(user=user)
    client.login(username='test_mrsfileuploadview_admins', password='secret')
    response = client.get(mrsrequest.pmt.get_download_url())
    assert response.status_code == 200

    user.caisses.remove(caisse)
    response = client.get(mrsrequest.pmt.get_download_url())
    assert response.status_code == 404
