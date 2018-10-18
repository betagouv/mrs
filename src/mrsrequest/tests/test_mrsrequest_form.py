import io

from dbdiff.fixture import Fixture
from freezegun import freeze_time
import pytest

from mrsattachment.models import MRSAttachment
from mrsrequest.forms import MRSRequestCreateForm
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
        data['distancevp'] = ['100']
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
    form = _form(expensevp=0)
    assert not form.non_field_errors()
    assert not form.is_valid()
    assert list(form.errors.keys()) == ['pmt']

    # Bills become required with expensevp
    form = _form(expensevp=10)
    assert not form.non_field_errors()
    assert not form.is_valid()
    assert list(form.errors.keys()) == ['pmt', 'bills']

    with io.BytesIO(b'test_mrsattachmentform0') as f:
        f.name = 'test_mrsattachmentform0.jpg'
        f.content_type = 'image/jpg'
        PMT.objects.record_upload(mrsrequest_uuid, f)

    # Only Bills is missing now
    form = _form(expensevp=10)
    assert not form.non_field_errors()
    assert not form.is_valid()
    assert list(form.errors.keys()) == ['bills']

    with io.BytesIO(b'test_mrsattachmentform1') as f:
        f.name = 'test_mrsattachmentform1.jpg'
        f.content_type = 'image/jpg'
        Bill.objects.record_upload(mrsrequest_uuid, f)

    # Is the form's save_m2m method going to relate the above uploads by
    # uuid ?
    form = _form(expensevp=10)
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
