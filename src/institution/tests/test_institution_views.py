from dbdiff.fixture import Fixture
from freezegun import freeze_time
import pytest

from django.urls import reverse

from institution.models import Institution
from institution.views import (
    InstitutionMRSRequestCreateView,
)
from mrsattachment.models import MRSAttachment
from mrsrequest.models import Bill, MRSRequest, PMT, Transport
from person.models import Person


finess = pytest.fixture(lambda: 310000000)
institution_uuid = pytest.fixture(
    lambda: 'aaadb065-0566-48be-822d-66bd3277d823')


@pytest.mark.django_db
def test_mrsrequest_create_view_finess_validation(client, finess):
    url = reverse('institution:mrsrequest_iframe', args=[finess])
    response = client.get(url)
    assert response.status_code == 404

    Institution.objects.create(finess=finess, origin='origin')
    response = client.get(url)
    assert response.status_code == 200
    assert response['X-Frame-Options'] == 'ALLOW-FROM origin'
    assert response['Access-Control-Allow-Origin'] == 'origin'


@pytest.mark.django_db
def test_mrsrequest_status_view(
        client, finess, mrsrequest_uuid, institution_uuid):

    url = reverse(
        'institution:mrsrequest_status',
        args=[finess, mrsrequest_uuid],
    )

    response = client.get(url)
    assert response.status_code == 404

    institution = Institution.objects.create(
        finess=finess,
        origin='origin',
        id=institution_uuid
    )
    response = client.get(url)
    assert response.status_code == 404

    MRSRequest.objects.create(
        id=mrsrequest_uuid,
        status=1,
        institution=institution,
    )
    response = client.get(url)
    assert response.status_code == 200
    assert response.content == b'{"status": 1}'


@freeze_time('2017-12-19 13:33:37')
@pytest.mark.dbdiff(models=[MRSAttachment, PMT, Person, Bill, Transport])
def test_mrsrequestcreateview_post_save_integration(
        p, finess, institution_uuid, caisse_with_region):

    data = dict(mrsrequest_uuid=p.mrsrequest.id)
    data['caisse'] = caisse_with_region.pk
    data['region'] = caisse_with_region.regions.first().pk
    data['trip_kind'] = 'return'
    data['iterative_number'] = 2
    data['transport-0-date_depart'] = '2017-02-02'
    data['transport-0-date_return'] = '2017-02-02'
    data['transport-1-date_depart'] = '2017-01-02'
    data['transport-1-date_return'] = '2017-01-02'
    data['distancevp'] = '100'
    data['expensevp_toll'] = '10'
    data['modevp'] = 'modevp'
    data['first_name'] = 'jamesy'
    data['last_name'] = 'wuzere'
    data['birth_date'] = '2007-02-07'
    data['email'] = 'jpic@yourlabs.org'
    data['use_email'] = False
    data['nir'] = '1234567890123'
    data['pmt_pel'] = 'pmt'

    # da key
    data['certify'] = True

    PMT.objects.create(
        mrsrequest_uuid=p.mrsrequest.id,
        filename='test_institutionmrsrequestcreateview_story.jpg',
        binary=b'test_institutionmrsrequestcreateview_story',
    )
    Bill.objects.create(
        mrsrequest_uuid=p.mrsrequest.id,
        filename='test_institutionmrsrequestcreateview_story.jpg',
        binary=b'test_institutionmrsrequestcreateview_story',
    )

    Institution.objects.create(finess=finess, id=institution_uuid, origin='o')
    p.view_class = InstitutionMRSRequestCreateView
    p.view_kwargs = {'finess': finess}
    p.url = reverse('institution:mrsrequest_iframe', args=[finess])
    p.post(**data)
    assert not p.view.form_errors()

    Fixture(
        './src/institution/tests/test_mrsrequest_iframe.json',  # noqa
        models=[MRSAttachment, MRSRequest, PMT, Person, Bill, Transport]
    ).assertNoDiff()
