import io

from dbdiff.fixture import Fixture
from freezegun import freeze_time
import pytest

from mrsattachment.models import MRSAttachment
from mrsrequest.forms import MRSRequestAdminForm
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
@pytest.mark.django_db
def test_form_save_m2m(monkeypatch, person):
    mrsrequest_uuid = '6bf490e6-4521-458a-adfe-8d4ef5a64687'

    monkeypatch.setattr(
        'mrsattachment.models.MRSAttachment.get_upload_body',
        lambda upload: upload.read()
    )

    with io.BytesIO(b'test_mrsattachmentform0') as f:
        f.name = 'test_mrsattachmentform0.jpg'
        f.content_type = 'image/jpg'
        PMT.objects.record_upload(mrsrequest_uuid, f)

    with io.BytesIO(b'test_mrsattachmentform1') as f:
        f.name = 'test_mrsattachmentform1.jpg'
        f.content_type = 'image/jpg'
        Bill.objects.record_upload(mrsrequest_uuid, f)

    data = dict(mrsrequest_uuid=[mrsrequest_uuid])
    data['date_depart'] = ['2017-02-02']
    data['date_return'] = ['2017-02-02']
    data['distance'] = ['100']
    data['expense'] = ['10']
    data['insured'] = [str(person.pk)]

    # If this test method goes wrong about the uuid, make sure its not
    # lost during ctor
    form = MRSRequestAdminForm(data)

    # Emulate what djang admin loves to do
    form.full_clean()
    assert not form.non_field_errors()
    assert not form.errors
    assert form.is_valid()

    obj = form.save(commit=False)
    form.save_m2m()
    obj.save()

    Fixture(
        './src/mrsrequest/tests/test_mrsrequest_form.json',  # noqa
        models=[MRSAttachment, MRSRequest, PMT, Person, Bill, Transport]
    ).assertNoDiff()
