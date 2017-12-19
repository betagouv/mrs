from dbdiff.fixture import Fixture
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
import pytest

from mrsrequest.models import MRSRequest
from mrsrequest.views import MRSRequestCreateView
from person.models import Person
from pmt.models import PMT
from transport.models import Bill, Transport


def test_mrsrequestcreateview_get(srf):
    request = srf.get(reverse('mrsrequest:wizard'))
    view = MRSRequestCreateView(request=request)
    response = view.dispatch(request)

    assert response.status_code == 200
    assert view.object.is_allowed(request)

    # This is what the user should post as mrsrequest_uuid
    assert view.mrsrequest_uuid == str(view.object.id)


class Payload(object):
    def __init__(self, srf):
        self.srf = srf
        self.mrsrequest = MRSRequest.objects.create(
            id='e29db065-0566-48be-822d-66bd3277d823'
        )

    def post(self, **data):
        self.request = self.srf.post(reverse('mrsrequest:wizard'), data)
        self.mrsrequest.allow(self.request)
        self.view = MRSRequestCreateView(request=self.request)
        self.response = self.view.dispatch(self.request)


@pytest.fixture
def p(srf):
    return Payload(srf)


@pytest.mark.django_db
def test_mrsrequestcreateview_has_perm_effect(p):
    p.post()
    assert p.response.status_code == 400

    p.post(mrsrequest_uuid='1234')
    assert p.response.status_code == 400
    assert not getattr(p.view, 'object', False)

    p.post(mrsrequest_uuid=p.mrsrequest.id)
    assert p.response.status_code == 200
    assert p.view.object


@pytest.mark.django_db
def test_mrsrequestcreateview_hydrate_pmt(p):
    p.post(mrsrequest_uuid=p.mrsrequest.id)
    assert not p.view.forms['pmt'].is_valid()

    p.mrsrequest.pmt = PMT.objects.create(
        mrsrequest=p.mrsrequest,
        filename='test_mrsrequestcreateview_story.jpg',
        binary=b'test_mrsrequestcreateview_story',
    )
    p.post(mrsrequest_uuid=p.mrsrequest.id)
    assert not p.view.forms['pmt'].errors
    assert p.view.forms['pmt'].is_valid()


@pytest.mark.django_db
def test_mrsrequestcreateview_hydrate_transport(p):
    data = dict(mrsrequest_uuid=p.mrsrequest.id)
    p.post(**data)
    assert not p.view.forms['transport'].is_valid()

    data['transportform-date_depart'] = '2017-02-02'
    data['transportform-date_return'] = '2017-02-02'
    data['transportform-distance'] = '100'
    data['transportform-expense'] = '0'
    p.post(**data)
    assert not p.view.forms['transport'].errors
    assert p.view.forms['transport'].is_valid()

    data['transportform-expense'] = '10'
    p.post(**data)
    assert list(p.view.forms['transport'].errors) == ['bills']
    assert not p.view.forms['transport'].is_valid()

    transport = p.mrsrequest.transport_set.create()
    transport.bill_set.create(
        filename='test_mrsrequestcreateview_story.jpg',
        binary=b'test_mrsrequestcreateview_story',
    )
    p.post(**data)
    assert not p.view.forms['transport'].errors
    assert p.view.forms['transport'].is_valid()


@pytest.mark.django_db
def test_mrsrequestcreateview_hydrate_person(p):
    data = dict(mrsrequest_uuid=p.mrsrequest.id)
    p.post(**data)
    assert not p.view.forms['person'].is_valid()

    data['personform-first_name'] = 'jamesy'
    data['personform-last_name'] = 'wuzere'
    data['personform-birth_date'] = '2007-02-07'
    data['personform-email'] = 'jpic@yourlabs.org'
    p.post(**data)
    assert not p.view.forms['person'].is_valid()

    data['personform-nir'] = '123412312'
    p.post(**data)
    assert not p.view.forms['person'].errors
    assert p.view.forms['person'].is_valid()


@freeze_time('2017-12-19 05:51:11')
@pytest.mark.django_db
def test_mrsrequestcreateview_save(p):
    p.mrsrequest.creation_datetime = timezone.now()
    p.mrsrequest.save()
    data = dict(mrsrequest_uuid=p.mrsrequest.id)
    data['transportform-date_depart'] = '2017-02-02'
    data['transportform-date_return'] = '2017-02-02'
    data['transportform-distance'] = '100'
    data['transportform-expense'] = '10'
    data['personform-first_name'] = 'jamesy'
    data['personform-last_name'] = 'wuzere'
    data['personform-birth_date'] = '2007-02-07'
    data['personform-email'] = 'jpic@yourlabs.org'
    data['personform-nir'] = '123412312'

    # da key
    data['certify'] = True

    p.mrsrequest.pmt = PMT.objects.create(
        mrsrequest=p.mrsrequest,
        filename='test_mrsrequestcreateview_story.jpg',
        binary=b'test_mrsrequestcreateview_story',
    )
    transport = p.mrsrequest.transport_set.create()
    transport.bill_set.create(
        filename='test_mrsrequestcreateview_story.jpg',
        binary=b'test_mrsrequestcreateview_story',
    )

    p.post(**data)

    Fixture(
        './src/mrsrequest/tests/test_mrsrequestcreateview_hydrate_transport.json',  # noqa
        models=[MRSRequest, PMT, Person, Bill, Transport]
    ).assertNoDiff()
