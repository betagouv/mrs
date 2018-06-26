import datetime
import io
import pytest
import pytz
from uuid import uuid4

from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage import default_storage
from django.contrib.sessions.backends.base import SessionBase
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test.client import RequestFactory as drf
from django.urls import reverse

from caisse.models import Caisse
from mrsrequest.models import MRSRequest
from mrsrequest.views import MRSRequestCreateView
from mrsuser.models import User


id = mrsrequest_uuid = pytest.fixture(
    lambda: '2b88b740-3920-44e9-b086-c851f58e7ea7')


@pytest.fixture
def su():
    return User.objects.update_or_create(
        username='su',
        defaults=dict(is_superuser=True)
    )[0]


class RequestFactory(drf):
    def __init__(self, user=None):
        self.user = user or AnonymousUser()
        super().__init__()

    def generic(self, *args, **kwargs):
        request = super().generic(*args, **kwargs)
        request.session = SessionBase()
        request.user = self.user
        request._messages = default_storage(request)
        return request


@pytest.fixture
def request_factory():
    return RequestFactory


@pytest.fixture
def srf():
    return RequestFactory(AnonymousUser())


@pytest.fixture
def admin():
    return RequestFactory(User.objects.update_or_create(
        username='test',
        defaults=dict(
            is_staff=True,
            is_superuser=True,
        ),
    )[0])


@pytest.fixture(scope='class')
def srf_class(request):
    request.cls.srf = srf()


@pytest.fixture
def uuid():
    return str(uuid4())


@pytest.fixture
def upload():
    return InMemoryUploadedFile(
        io.BytesIO(b'aoeu'),
        'field_name',
        'foo.png',
        'image/png',
        4,  # length of b'aoeu'
        None,
    )


class Payload(object):
    def __init__(self, srf):
        self.srf = srf
        self.mrsrequest = MRSRequest(
            id='e29db065-0566-48be-822d-66bd3277d823'
        )
        self.url = reverse('mrsrequest:wizard')
        self.view_class = MRSRequestCreateView
        self.view_kwargs = dict()

    def post(self, **data):
        self.request = self.srf.post(self.url, data)
        self.mrsrequest.allow(self.request)
        self.view = self.view_class(request=self.request, **self.view_kwargs)
        self.response = self.view.dispatch(self.request, **self.view_kwargs)


@pytest.fixture
def p(srf):
    return Payload(srf)


@pytest.fixture
def caisse():
    return Caisse.objects.update_or_create(
        pk=9,
        defaults=dict(
            code='010000000',
            number=311,
            name='test',
            active=True,
            liquidation_email='taoeu@aoeu.com',
        )
    )[0]


@pytest.fixture
def other_caisse():
    return Caisse.objects.update_or_create(
        pk=10,
        defaults=dict(
            code='110000000',
            number=333,
            name='test inactive',
            active=False,
        )
    )[0]
