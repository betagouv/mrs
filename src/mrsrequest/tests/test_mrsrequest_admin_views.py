import pytest

from crudlfap import crudlfap
from crudlfap_auth.crudlfap import User

from dbdiff.fixture import Fixture

from django.contrib.admin.models import LogEntry
from django import http

from freezegun import freeze_time

from caisse.models import Caisse
from mrsemail.models import EmailTemplate
from mrsrequest.models import MRSRequest, PMT
from person.models import Person


VIEWS = [
    'progress',
    'reject',
    'validate',
    'detail'
]


def view(v):
    return crudlfap.site['mrsrequest.mrsrequest'][v].as_view()


@pytest.fixture
def ur(request_factory):
    def user_request(method=None, **kwargs):
        user = None
        if kwargs:
            caisse = None
            if 'caisse' in kwargs:
                caisse = kwargs.pop('caisse')
            kwargs.setdefault('username', str(kwargs))
            user = User.objects.get_or_create(**kwargs)[0]
            if caisse:
                user.caisses.add(caisse)
                if 'profile' not in kwargs:
                    user.profile = 'upn'
        return getattr(request_factory(user), method or 'get')('/path')
    return user_request


@pytest.mark.dbdiff(models=[LogEntry, Caisse, Person])
@pytest.fixture
def mrsrequest():
    uuid = '4255e33f-88c0-4dbf-b8ee-69cb283a7cea'
    with freeze_time('3000-12-31 13:37:42'):
        mrsrequest = MRSRequest.objects.create(
            pk=uuid,
            caisse=Caisse.objects.create(name='adminviews', number=9),
            insured=Person.objects.create(
                email='t@tt.tt',
                nir=111111111111,
            ),
            pmt=PMT.objects.create(
                mrsrequest_uuid=uuid,
                filename='test_mrsrequest_admin_views.jpg',
                binary=b'test_mrsrequest_admin_views',
            )
        )
        mrsrequest.pmt.mrsrequest = mrsrequest
        mrsrequest.pmt.save()
    return mrsrequest


@pytest.fixture
def emailtemplate():
    return EmailTemplate.objects.get_or_create(
        name='reject',
        subject='reject {{ display_id }}',
        body='reject {{ display_id }}',
    )[0]


@pytest.mark.django_db
@pytest.mark.parametrize('v', VIEWS + ['list'])
def test_validate_redirects_anonymous(v, ur, mrsrequest):
    response = view('validate')(ur(), pk=mrsrequest.pk)
    assert response.status_code == 302
    assert 'login' in response['Location']


@pytest.mark.django_db
@pytest.mark.parametrize('v', VIEWS)
def test_redirects_for_non_caisse_staff(v, ur, mrsrequest):
    response = view(v)(ur(), pk=mrsrequest.pk)
    assert response.status_code == 302
    assert 'login' in response['Location']


@pytest.mark.django_db
@pytest.mark.parametrize('v', ['detail', 'progress', 'reject'])
def test_get_200_for_caisse_staff(v, ur, mrsrequest):
    response = view(v)(ur(caisse=mrsrequest.caisse), pk=mrsrequest.pk)
    assert response.status_code == 200


@pytest.mark.django_db
def test_validate_get_fail_if_not_inprogress(ur, mrsrequest):
    with pytest.raises(http.Http404):
        view('validate')(ur(caisse=mrsrequest.caisse), pk=mrsrequest.pk)


@pytest.mark.django_db
def test_progress_post_fails_for_non_caisse_staff(ur, mrsrequest):
    with pytest.raises(http.Http404):
        view('progress')(ur('post', profile='upn'), pk=mrsrequest.pk)


@freeze_time('3000-12-31 13:37:42')
@pytest.mark.dbdiff(models=[LogEntry, Caisse, Person])
def test_progress_validate_success(ur, mrsrequest):
    request = ur('post', caisse=mrsrequest.caisse)
    view('progress')(request, pk=mrsrequest.pk)
    with pytest.raises(http.Http404):
        view('progress')(request, pk=mrsrequest.pk)

    # test in_status_by
    result = list(MRSRequest.objects.all().in_status_by(
        'inprogress', request.user))
    assert len(result) == 1
    assert str(result[0].pk) == str(mrsrequest.pk)

    response = view('validate')(request, pk=mrsrequest.pk)
    assert response['Location'] == mrsrequest.get_absolute_url()

    Fixture(
        './src/mrsrequest/tests/test_mrsrequest_admin_progress_validate.json',  # noqa
        models=[MRSRequest, LogEntry]
    ).assertNoDiff()

    for v in ('progress', 'reject', 'validate'):
        with pytest.raises(http.Http404):
            view(v)(request, pk=mrsrequest.pk)


@freeze_time('3000-12-31 13:37:42')
@pytest.mark.dbdiff(models=[LogEntry, Caisse, Person, EmailTemplate])
def test_progress_reject_success(ur, mrsrequest, emailtemplate):
    request = ur('post', caisse=mrsrequest.caisse)
    view('progress')(request, pk=mrsrequest.pk)
    with pytest.raises(http.Http404):
        view('progress')(request, pk=mrsrequest.pk)

    request.POST = dict(
        template=emailtemplate.pk,
        subject='reject {}'.format(mrsrequest.pk),
        body='reject body {}'.format(mrsrequest.pk),
    )
    response = view('reject')(request, pk=mrsrequest.pk)
    assert response['Location'] == mrsrequest.get_absolute_url()

    Fixture(
        './src/mrsrequest/tests/test_mrsrequest_admin_progress_reject.json',  # noqa
        models=[MRSRequest, LogEntry]
    ).assertNoDiff()

    for v in ('progress', 'reject', 'validate'):
        with pytest.raises(http.Http404):
            view(v)(request, pk=mrsrequest.pk)
