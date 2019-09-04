import copy
import io

from dbdiff.fixture import Fixture
from freezegun import freeze_time
import pytest

from mrsattachment.models import MRSAttachment
from mrsrequest.forms import (
    MRSRequestCreateForm,
    TransportFormSet,
)
from mrsrequest.models import Bill, MRSRequest, PMT, Transport
from person.models import Person


@pytest.fixture
def person():
    return Person.objects.create(**{
        'birth_date': '2007-02-07',
        'email': 'jpic@yourlabs.org',
        'first_name': 'jamesy',
        'last_name': 'wuzere',
        'nir': 1234567890123
    })


@freeze_time('2017-12-19 05:51:11')
@pytest.mark.dbdiff(models=[MRSAttachment, PMT, Person, Bill, Transport])
def test_form_save_m2m(monkeypatch, person, caisse):
    def _form(**extra):
        data = dict()
        data['caisse'] = [caisse.pk]
        data['region'] = [caisse.regions.first().pk]
        data['distancevp'] = ['100']
        data['pmt_pel'] = ['pmt']

        if 'expenseatp' in extra:
            data['modeatp'] = ['modeatp']

        if 'expensevp_toll' in extra or 'expensevp_parking' in extra:
            data['modevp'] = ['modevp']

        for k, v in extra.items():
            data[k] = [str(v)]

        form = MRSRequestCreateForm(data, mrsrequest_uuid=mrsrequest_uuid)

        form.full_clean()
        return form

    mrsrequest_uuid = '6bf490e6-4521-458a-adfe-8d4ef5a64687'

    monkeypatch.setattr(
        'mrsattachment.models.MRSAttachment.get_upload_body',
        lambda upload: upload.read()
    )

    # PMT is only missing attachement at 0 expensevp
    form = _form(expensevp_toll=0)
    assert not form.non_field_errors()
    assert not form.is_valid()
    assert list(form.errors.keys()) == ['pmt']

    # Bills become required with expensevp
    form = _form(expensevp_toll=10)
    assert not form.non_field_errors()
    assert not form.is_valid()
    assert list(form.errors.keys()) == ['pmt', 'billvps']

    with io.BytesIO(b'test_mrsattachmentform0') as f:
        f.name = 'test_mrsattachmentform0.jpg'
        f.content_type = 'image/jpg'
        PMT.objects.record_upload(mrsrequest_uuid, f)

    # Only Bills is missing now
    form = _form(expensevp_toll=10)
    assert not form.non_field_errors()
    assert not form.is_valid()
    assert list(form.errors.keys()) == ['billvps']

    for mode in ['vp', 'atp']:
        with io.BytesIO(b'test_mrsattachmentform1') as f:
            f.name = f'test_mrsattachmentform1_{mode}.jpg'
            f.content_type = 'image/jpg'
            Bill.objects.record_upload(mrsrequest_uuid, f, mode=mode)

    # Is the form's save_m2m method going to relate the above uploads by
    # uuid ?
    # We also check integer values, decimal values with dots and decimal values
    # with commas are valid
    form = _form(expensevp_toll="10", expensevp_parking="21,3",
                 expenseatp="10.6")
    assert not form.non_field_errors()
    assert not form.errors
    assert form.is_valid()

    obj = form.save(commit=False)  # let's try that false commit,
    obj.save()                     # with manual save,
    form.save_m2m()                # and manual relation save.

    Fixture(
        './src/mrsrequest/tests/test_mrsrequest_form.json',  # noqa
        models=[MRSAttachment, MRSRequest, PMT, Person, Bill, Transport]
    ).assertNoDiff()


def person_transport_formset():
    Fixture('./src/mrs/tests/data.json').load()
    person = Person.objects.get(pk=4)
    formset = TransportFormSet({
        # base new one, should not have duplicate errors
        'transport-0-date_depart': '2018-05-01',
        'transport-0-date_return': '2018-05-02',
        # this one should not raise any error
        'transport-1-date_depart': '2018-06-01',
        'transport-1-date_return': '2018-06-02',
        # this should be detected as duplicate of transport-0
        'transport-2-date_depart': '2018-05-01',
        'transport-2-date_return': '2018-05-02',
        # this depart should be detected as dupe of return-0
        'transport-3-date_depart': '2018-05-02',
        'transport-3-date_return': '2018-05-07',
        # this return should be detected as dupe of depart-0
        'transport-4-date_depart': '2018-04-02',
        'transport-4-date_return': '2018-05-01',
        'iterative_number': '5',
    })

    formset.full_clean()  # make cleaned_data

    for form in formset.forms:
        # let's keep a copy of those for assertions
        form.cleaned_data_copy = copy.copy(form.cleaned_data)

    return person, formset


@pytest.mark.django_db
def test_transport_formset_is_valid():
    person, formset = person_transport_formset()
    assert formset.is_valid()


@pytest.mark.django_db
def test_transport_formset_confirms_invalidates():
    person, formset = person_transport_formset()
    formset.add_confirms(person.nir, person.birth_date)

    # given the above person already have submited dates in
    # a validated request, add_confirms should have added
    # errors.
    assert not formset.is_valid()


@pytest.mark.django_db  # noqa
def test_transport_formset_add_confirms():
    """Assert that it will generate proper confirms structure."""
    person, formset = person_transport_formset()
    formset.add_confirms(person.nir, person.birth_date)

    # ok it's a bit overkill but keep in mind this is critical to be done right
    # for the user experience, and there also are (light, but significant)
    # security implications
    for form in formset.forms:
        data = form.cleaned_data_copy

        for field, confirms in form.confirms.items():
            for confirm, confirm_data in confirms.items():
                if confirm == 'inprogress':
                    for transport in confirm_data:
                        mrsrequest = transport.mrsrequest

                        # basic security test are going to be omnipresent here
                        assert mrsrequest.insured == person
                        # check that the mrsrequest has the right status
                        assert mrsrequest.status_in('new', 'inprogress')
                        # check that the transport in question does have a
                        # matching date
                        assert getattr(transport, field) == data.get(field)

                elif confirm == 'validated':
                    for transport in confirm_data:
                        mrsrequest = transport.mrsrequest

                        assert mrsrequest.insured == person
                        assert mrsrequest.status_in('validated')
                        assert getattr(transport, field) == data.get(field)

                elif confirm == 'duplicate':
                    for form_number, form_field in confirm_data:
                        compare = formset.forms[form_number].cleaned_data_copy
                        assert compare[form_field] == data[field]


@pytest.mark.django_db
def test_transport_formset_confirm_messages():
    person, formset = person_transport_formset()
    formset.add_confirms(person.nir, person.birth_date)

    assert formset.errors[0] == dict(
        date_depart=[
            ' '.join([
                'Ce trajet vous a été réglé lors des demandes du 03/05/2018',
                'n° 201805030001 et du 03/05/2018 n° 201805030000.'
            ]),
            ' '.join([
                'Votre demande de prise en charge pour ce trajet est en cours',
                'de traitement dans la demande du 02/05/2018 n° 201805020001.'
            ]),
        ]
    )
    assert formset.errors[1] == dict()
    assert formset.errors[2] == dict(
        date_depart=[
            'Date de trajet déjà présente dans le trajet aller n° 1.',
            ' '.join([
                'Ce trajet vous a été réglé lors des demandes du 03/05/2018',
                'n° 201805030001 et du 03/05/2018 n° 201805030000.',
            ]),
            ' '.join([
                'Votre demande de prise en charge pour ce trajet est en cours',
                'de traitement dans la demande du 02/05/2018 n° 201805020001.'
            ]),
        ],
        date_return=[
            'Date de trajet déjà présente dans le trajet retour n° 1.',
        ]
    )
    assert formset.errors[3] == dict(
        date_depart=[
            ' '.join([
                'Date de trajet déjà présente dans les trajets',
                'retour n° 1 et retour n° 3.',
            ]),
            ' '.join([
                'Ce trajet vous a été réglé lors de la demande du 03/05/2018',
                'n° 201805030000.',
            ]),
        ]
    )
    assert formset.errors[4] == dict(
        date_return=[
            ' '.join([
                'Date de trajet déjà présente dans les trajets',
                'aller n° 1 et aller n° 3.',
            ])
        ],
    )
