from datetime import date
from dbdiff.fixture import Fixture
from django.urls import reverse
from freezegun import freeze_time
import os
import pytest

from mrsattachment.models import MRSAttachment
from mrsrequest.models import (
    Bill, BillATP, BillVP, MRSRequest, PMT, Transport)
from mrsrequest.views import MRSRequestCreateView
from mrsstat.models import Stat
from person.models import Person


def test_mrsrequestcreateview_get(srf):
    request = srf.get(reverse('mrsrequest:wizard'))
    view = MRSRequestCreateView(request=request)
    response = view.dispatch(request)

    assert response.status_code == 200
    assert view.object.is_allowed(request)

    # This is what the user should post as mrsrequest_uuid
    assert view.mrsrequest_uuid == str(view.object.id)


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
def test_mrsrequestcreateview_requires_pmt_by_default(p, upload):
    p.post(mrsrequest_uuid=p.mrsrequest.id)
    assert 'pel' not in p.view.forms['mrsrequest'].errors
    assert 'pmt' in p.view.forms['mrsrequest'].errors

    p.mrsrequest.pmt = PMT.objects.create(
        mrsrequest_uuid=p.mrsrequest.id,
        filename='test_mrsrequestcreateview_story.jpg',
        attachment_file=upload
    )
    p.post(mrsrequest_uuid=p.mrsrequest.id)
    assert 'pmt' not in p.view.forms['mrsrequest'].errors


@pytest.mark.django_db
def test_mrsrequestcreateview_requires_pel(p):
    p.post(mrsrequest_uuid=p.mrsrequest.id, pmt_pel='pel')
    assert 'pel' in p.view.forms['mrsrequest'].errors
    assert 'pmt' not in p.view.forms['mrsrequest'].errors


@pytest.mark.django_db
def test_mrsrequestcreateview_pel_validation(p):
    p.post(
        mrsrequest_uuid=p.mrsrequest.id,
        pmt_pel='pel',
        pel='aoeuaoeua$e123'
    )
    assert 'pel' in p.view.forms['mrsrequest'].errors
    assert 'pmt' not in p.view.forms['mrsrequest'].errors

    p.post(
        mrsrequest_uuid=p.mrsrequest.id,
        pmt_pel='pel',
        pel='aoeuaoeuaoe123'
    )
    assert 'pel' not in p.view.forms['mrsrequest'].errors
    assert 'pmt' not in p.view.forms['mrsrequest'].errors


@pytest.mark.django_db
def test_mrsrequestcreateview_requires_iterative_number_gt_0(p):
    p.post(
        mrsrequest_uuid=p.mrsrequest.id,
        iterative_show=1,
        iterative_number=0,
        trip_kind='simple',
    )
    form = p.view.forms['transport']
    assert not form.is_valid()
    assert 'iterative_number' in form.errors


@pytest.mark.django_db
def test_mrsrequestcreateview_requires_transport_date(p):
    p.post(mrsrequest_uuid=p.mrsrequest.id, iterative_number=0)
    assert not p.view.forms['transport_formset'].is_valid()


@freeze_time('2017-12-19 05:51:11')
@pytest.mark.django_db
def test_mrsrequestcreateview_pel_integration(p, caisse, upload):
    data = form_data(
        upload=upload,
        mrsrequest_uuid=p.mrsrequest.id,
        pmt_pel='pel',
        caisse=caisse.pk,
        region=caisse.regions.first().pk,
        pel='aoeuaoeuaoe123',
    )
    p.post(**data)
    assert MRSRequest.objects.get(pk=p.mrsrequest.id).pel == 'aoeuaoeuaoe123'


@freeze_time('2017-12-19 05:51:11')
@pytest.mark.django_db
def test_mrsrequestcreateview_convocation_integration(p, caisse, upload):
    data = form_data(
        upload=upload,
        mrsrequest_uuid=p.mrsrequest.id,
        pmt_pel='convocation',
        caisse=caisse.pk,
        region=caisse.regions.first().pk,
        convocation='12/12/2017',
    )
    p.post(**data)
    assert MRSRequest.objects.get(
        pk=p.mrsrequest.id
    ).convocation == date(2017, 12, 12)


@pytest.mark.django_db
def test_mrsrequestcreateview_hydrate_mrsrequest(p, caisse, upload):
    data = dict(mrsrequest_uuid=p.mrsrequest.id)
    p.post(**data)
    assert not p.view.forms['mrsrequest'].is_valid()

    data['caisse'] = caisse.pk
    data['region'] = caisse.regions.first().pk
    data['transport-1-date_depart'] = '2017-02-02'
    data['transport-1-date_return'] = '2017-02-02'
    data['trip_kind'] = 'return'
    data['modevp'] = 'modevp'
    data['distancevp'] = '100'
    data['expensevp_toll'] = '0'
    data['pmt_pel'] = 'pmt'
    p.mrsrequest.pmt = PMT.objects.create(
        mrsrequest_uuid=p.mrsrequest.id,
        filename='test_mrsrequestcreateview_story.jpg',
        attachment_file=upload
    )
    p.post(**data)
    assert not p.view.forms['mrsrequest'].errors
    assert p.view.forms['mrsrequest'].is_valid()

    data['expensevp_toll'] = '10'
    p.post(**data)
    assert list(p.view.forms['mrsrequest'].errors) == ['billvps']
    assert not p.view.forms['mrsrequest'].is_valid()

    BillVP.objects.create(
        mrsrequest_uuid=p.mrsrequest.id,
        filename='test_mrsrequestcreateview_story.jpg',
        attachment_file=upload
    )
    p.post(**data)
    assert not p.view.forms['mrsrequest'].errors
    assert p.view.forms['mrsrequest'].is_valid()


@pytest.mark.django_db
def test_mrsrequestcreateview_hydrate_person(p):
    data = dict(mrsrequest_uuid=p.mrsrequest.id)
    p.post(**data)
    assert not p.view.forms['person'].is_valid()

    data['first_name'] = 'jamesy'
    data['last_name'] = 'wuzere'
    data['birth_date'] = '2007-02-07'
    data['email'] = 'jpic@yourlabs.org'
    p.post(**data)
    assert not p.view.forms['person'].is_valid()

    data['nir'] = '1234567890123'
    p.post(**data)
    assert not p.view.forms['person'].errors
    assert p.view.forms['person'].is_valid()


def form_data(upload, **data):
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
    data['certify'] = True
    data.setdefault('pmt_pel', 'pmt')

    PMT.objects.create(
        mrsrequest_uuid=data['mrsrequest_uuid'],
        filename='test_mrsrequestcreateview_story.jpg',
        attachment_file=upload
    )
    BillVP.objects.create(
        mrsrequest_uuid=data['mrsrequest_uuid'],
        filename='test_mrsrequestcreateview_story.jpg',
        attachment_file=upload
    )
    return data


@freeze_time('2017-12-19 05:51:11')
@pytest.mark.dbdiff(models=[MRSAttachment, PMT, Person, Bill, Transport])
def test_mrsrequestcreateview_modevp_post_save_integration(p, caisse, upload):
    data = form_data(
        upload=upload,
        mrsrequest_uuid=p.mrsrequest.id,
        caisse=caisse.pk,
        region=caisse.regions.first().pk
    )

    p.post(**data)

    Fixture(
        './src/mrsrequest/tests/test_mrsrequestcreateview_modevp.json',
        models=[MRSAttachment, MRSRequest, PMT, Person, Bill, Transport]
    ).assertNoDiff()


@freeze_time('2017-12-19 05:51:11')
@pytest.mark.django_db
def test_mrsrequestcreateview_email(p, caisse, mailoutbox, mocker, upload):
    data = form_data(
        upload=upload,
        mrsrequest_uuid=p.mrsrequest.id,
        caisse=caisse.pk,
        region=caisse.regions.first().pk,
        distancevp=p.mrsrequest.distancevp
    )
    p.post(**data)
    url = os.path.join(
        'http://localhost:8000',
        'annuler-demande',
        'e29db065-0566-48be-822d-66bd3277d823/',
    )
    assert url in mailoutbox[0].body
    assert caisse.liquidation_email in mailoutbox[0].reply_to
    assert len(mailoutbox[0].reply_to) == 1

    texte_km_declares = "L'Assurance Maladie va analyser votre demande de " \
                        "remboursement sur la base du nombre total de " \
                        "kilomètres déclarés, soit {}."\
        .format("100")
    assert texte_km_declares in mailoutbox[0].body


@freeze_time('2017-12-19 05:51:11')
@pytest.mark.dbdiff(models=[MRSAttachment, PMT, Person, Bill, Transport])
def test_mrsrequestcreateview_modeatp_post_save_integration(p, caisse, upload):
    data = form_data(
        upload=upload,
        mrsrequest_uuid=p.mrsrequest.id,
        caisse=caisse.pk,
        region=caisse.regions.first().pk
    )
    data['expensevp_toll'] = ''
    data['expenseatp'] = '10'
    data['modevp'] = ''
    data['modeatp'] = 'modeatp'
    BillATP.objects.create(
        mrsrequest_uuid=data['mrsrequest_uuid'],
        filename='test_mrsrequestcreateview_story.jpg',
        attachment_file=upload
    )

    p.post(**data)

    Fixture(
        './src/mrsrequest/tests/test_mrsrequestcreateview_modeatp.json',
        models=[MRSAttachment, MRSRequest, PMT, Person, Bill, Transport]
    ).assertNoDiff()


@freeze_time('2017-12-19 05:51:11')
@pytest.mark.dbdiff(models=[MRSAttachment, PMT, Person, Bill, Transport])
def test_mrsrequestcreateview_empty_expenseatp(p, caisse, upload):
    data = form_data(
        upload=upload,
        mrsrequest_uuid=p.mrsrequest.id,
        caisse=caisse.pk
    )
    data['expenseatp'] = ''
    p.post(**data)


@freeze_time('2017-12-19 05:51:11')
@pytest.mark.django_db
def test_mrsrequestcreateview_post_save_integration_confirms_count(p, caisse,
                                                                   upload):
    data = form_data(
        upload=upload,
        mrsrequest_uuid=p.mrsrequest.id,
        caisse=caisse.pk,
        region=caisse.regions.first().pk
    )

    # Let's get started with two conflicts from inside the same request
    data['transport-1-date_depart'] = data['transport-0-date_depart']
    data['transport-1-date_return'] = data['transport-0-date_return']
    p.post(**data)
    assert p.view.conflicts_count == 2

    # should touch the daily conflicted counter only
    for _caisse in [caisse, None]:
        stat = Stat.objects.get(date='2017-12-19', caisse=_caisse)
        assert stat.mrsrequest_count_conflicted == 1
        assert stat.mrsrequest_count_conflicting == 0
        # well, until the user actually posts request, it's counted as resolved
        assert stat.mrsrequest_count_resolved == 1

    # Resolve one conflict and confirm it's fine
    data['transport-1-date_return'] = '03/02/2017'
    data['confirm'] = '1'
    p.post(**data)
    assert not p.view.form_errors()
    assert p.view.conflicts_count == 1

    # conflicting counter should increment now .....
    for _caisse in [caisse, None]:
        stat = Stat.objects.get(date='2017-12-19', caisse=_caisse)
        assert stat.mrsrequest_count_conflicted == 1
        assert stat.mrsrequest_count_conflicting == 1
        # .... which decreases the number of resolved conflicts to 0 !
        assert stat.mrsrequest_count_resolved == 0

    # View should see one resolved and one accepted conflict
    assert p.view.forms['mrsrequest'].instance.conflicts_resolved == 1
    assert p.view.forms['mrsrequest'].instance.conflicts_accepted == 1

    # Let's duplicate this request, only first trip should be conflicting
    p.mrsrequest = MRSRequest()
    data = form_data(
        upload=upload,
        mrsrequest_uuid=p.mrsrequest.id,
        caisse=caisse.pk,
        region=caisse.regions.first().pk
    )
    p.post(**data)
    assert p.view.conflicts_count == 1

    # conflicted counter should increase, resolved too (temporarily) and
    # conflicting should stall
    for _caisse in [caisse, None]:
        stat = Stat.objects.get(date='2017-12-19', caisse=_caisse)
        assert stat.mrsrequest_count_conflicted == 2
        assert stat.mrsrequest_count_conflicting == 1
        # increase again, temporary
        assert stat.mrsrequest_count_resolved == 1

    # Resolve that conflicts with new dates for first  transport
    data['confirm'] = '1'
    data['transport-0-date_depart'] = '03/01/2017'
    data['transport-0-date_return'] = '03/01/2017'
    p.post(**data)
    assert not p.view.form_errors()
    assert p.view.conflicts_count == 0

    # Insured has resolved a new conflict and not accepted any new one
    assert p.view.forms['mrsrequest'].instance.conflicts_resolved == 1
    assert p.view.forms['mrsrequest'].instance.conflicts_accepted == 0

    # conflicted counter should not move (conflict_count = 0)
    for _caisse in [caisse, None]:
        stat = Stat.objects.get(date='2017-12-19', caisse=_caisse)
        assert stat.mrsrequest_count_conflicted == 2
        assert stat.mrsrequest_count_conflicting == 1
        # user did post with all conflicts resolved, maintain the number
        assert stat.mrsrequest_count_resolved == 1

    # While we're at it try just to increment accepted conflicts
    p.mrsrequest = MRSRequest()
    data = form_data(
        upload=upload,
        mrsrequest_uuid=p.mrsrequest.id,
        caisse=caisse.pk,
        region=caisse.regions.first().pk
    )
    p.post(**data)
    # We're duplicating both Transport dates ...
    assert p.view.conflicts_count == 2

    # conflicting counter should increment
    for _caisse in [caisse, None]:
        stat = Stat.objects.get(date='2017-12-19', caisse=_caisse)
        assert stat.mrsrequest_count_conflicted == 3
        assert stat.mrsrequest_count_conflicting == 1
        # so far not submitted: temporary increase
        assert stat.mrsrequest_count_resolved == 2

    # ... and fixing only the second one
    data['transport-1-date_depart'] = '01/01/2017'
    data['transport-1-date_return'] = '01/01/2017'
    data['confirm'] = '1'
    p.post(**data)
    assert not p.view.form_errors()
    assert p.view.conflicts_count == 1

    # We so have resolved one conflict and accepted one conflict
    assert p.view.forms['mrsrequest'].instance.conflicts_resolved == 1
    assert p.view.forms['mrsrequest'].instance.conflicts_accepted == 1

    # conflicted counter should increment
    for _caisse in [caisse, None]:
        stat = Stat.objects.get(date='2017-12-19', caisse=_caisse)
        assert stat.mrsrequest_count_conflicted == 3
        assert stat.mrsrequest_count_conflicting == 2
        # request was posted with a conflict which decreases that number
        assert stat.mrsrequest_count_resolved == 1
