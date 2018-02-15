import io
import pytest
from uuid import uuid4

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.base import SessionBase
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test.client import RequestFactory as drf
from django.urls import reverse

from mrsrequest.models import MRSRequest
from mrsrequest.views import MRSRequestCreateView


id = mrsrequest_uuid = pytest.fixture(
    lambda: '2b88b740-3920-44e9-b086-c851f58e7ea7')


class RequestFactory(drf):
    def __init__(self, user):
        self.user = user
        super().__init__()

    def generic(self, *args, **kwargs):
        request = super().generic(*args, **kwargs)
        request.session = SessionBase()
        request.user = self.user
        return request


@pytest.fixture
def srf():
    return RequestFactory(AnonymousUser())


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
