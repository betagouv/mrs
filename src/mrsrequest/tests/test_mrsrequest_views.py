from dbdiff.fixture import Fixture
from django.urls import reverse
from freezegun import freeze_time
import pytest

from mrsattachment.models import MRSAttachment
from mrsrequest.models import Bill, MRSRequest, PMT, Transport
from mrsrequest.views import MRSRequestCreateView
from person.models import Person


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
        self.mrsrequest = MRSRequest(
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


def test_mrsrequestcreateview_post_fail_without_uuid(srf):
    request = srf.post('/')
    response = MRSRequestCreateView(request=request).dispatch(request)
    assert response.status_code == 400


def test_mrsrequestcreateview_post_fail_with_malformated_uuid(srf):
    request = srf.post('/', dict(mrsrequest_uuid='123'))
    response = MRSRequestCreateView(request=request).dispatch(request)
    assert response.status_code == 400


@pytest.mark.django_db
def test_mrsrequestcreateview_post_fail_with_unallowed_uuid(srf):
    request = srf.post('/', dict(
        mrsrequest_uuid='e29db065-0566-48be-822d-66bd3277d823'))
    response = MRSRequestCreateView(request=request).dispatch(request)
    assert response.status_code == 400


@pytest.mark.django_db
def test_mrsrequestcreateview_post_fail_with_existing_uuid(srf):
    m = MRSRequest.objects.create(id='e29db065-0566-48be-822d-66bd3277d823')
    request = srf.post('/', dict(mrsrequest_uuid=m.id))
    response = MRSRequestCreateView(request=request).dispatch(request)
    assert response.status_code == 400


@pytest.mark.django_db
def test_mrsrequestcreateview_post_fail_with_existing_allowed_uuid(srf):
    m = MRSRequest.objects.create(id='e29db065-0566-48be-822d-66bd3277d823')
    request = srf.post('/', dict(mrsrequest_uuid=m.id))
    m.allow(request)
    response = MRSRequestCreateView(request=request).dispatch(request)
    assert response.status_code == 400


@pytest.mark.django_db
def test_mrsrequestcreateview_post_responds_with_new_and_allowed_uuid(srf):
    m = MRSRequest(id='e29db065-0566-48be-822d-66bd3277d823')
    request = srf.post('/', dict(mrsrequest_uuid=m.id))
    m.allow(request)
    response = MRSRequestCreateView(request=request).dispatch(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_mrsrequestcreateview_requires_pmt(p):
    p.post(mrsrequest_uuid=p.mrsrequest.id)
    assert 'pmt' in p.view.forms['mrsrequest'].errors

    p.mrsrequest.pmt = PMT.objects.create(
        mrsrequest=p.mrsrequest,
        mrsrequest_uuid=p.mrsrequest.id,
        filename='test_mrsrequestcreateview_story.jpg',
        binary=b'test_mrsrequestcreateview_story',
    )
    p.post(mrsrequest_uuid=p.mrsrequest.id)
    assert 'pmt' not in p.view.forms['mrsrequest'].errors


@pytest.mark.django_db
def test_mrsrequestcreateview_hydrate_mrsrequest(p):
    data = dict(mrsrequest_uuid=p.mrsrequest.id)
    p.post(**data)
    assert not p.view.forms['mrsrequest'].is_valid()

    data['mrsrequestform-date_depart'] = '2017-02-02'
    data['mrsrequestform-date_return'] = '2017-02-02'
    data['mrsrequestform-distance'] = '100'
    data['mrsrequestform-expense'] = '0'
    p.mrsrequest.pmt = PMT.objects.create(
        mrsrequest=p.mrsrequest,
        mrsrequest_uuid=p.mrsrequest.id,
        filename='test_mrsrequestcreateview_story.jpg',
        binary=b'test_mrsrequestcreateview_story',
    )
    p.post(**data)
    assert not p.view.forms['mrsrequest'].errors
    assert p.view.forms['mrsrequest'].is_valid()

    data['mrsrequestform-expense'] = '10'
    p.post(**data)
    assert list(p.view.forms['mrsrequest'].errors) == ['bills']
    assert not p.view.forms['mrsrequest'].is_valid()

    p.mrsrequest.bill_set.create(
        mrsrequest_uuid=p.mrsrequest.id,
        filename='test_mrsrequestcreateview_story.jpg',
        binary=b'test_mrsrequestcreateview_story',
    )
    p.post(**data)
    assert not p.view.forms['mrsrequest'].errors
    assert p.view.forms['mrsrequest'].is_valid()


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

    data['personform-nir'] = '1234567890123'
    p.post(**data)
    assert not p.view.forms['person'].errors
    assert p.view.forms['person'].is_valid()


@freeze_time('2017-12-19 05:51:11')
@pytest.mark.django_db
def test_mrsrequestcreateview_save(p):
    data = dict(mrsrequest_uuid=p.mrsrequest.id)
    data['mrsrequestform-date_depart'] = '2017-02-02'
    data['mrsrequestform-date_return'] = '2017-02-02'
    data['mrsrequestform-distance'] = '100'
    data['mrsrequestform-expense'] = '10'
    data['personform-first_name'] = 'jamesy'
    data['personform-last_name'] = 'wuzere'
    data['personform-birth_date'] = '2007-02-07'
    data['personform-email'] = 'jpic@yourlabs.org'
    data['personform-nir'] = '1234567890123'

    # da key
    data['certify'] = True

    PMT.objects.create(
        mrsrequest_uuid=p.mrsrequest.id,
        filename='test_mrsrequestcreateview_story.jpg',
        binary=b'test_mrsrequestcreateview_story',
    )
    Bill.objects.create(
        mrsrequest_uuid=p.mrsrequest.id,
        filename='test_mrsrequestcreateview_story.jpg',
        binary=b'test_mrsrequestcreateview_story',
    )

    p.post(**data)

    Fixture(
        './src/mrsrequest/tests/test_mrsrequestcreateview_hydrate_mrsrequest.json',  # noqa
        models=[MRSAttachment, MRSRequest, PMT, Person, Bill, Transport]
    ).assertNoDiff()
