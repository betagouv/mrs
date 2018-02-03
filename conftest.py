import io
import pytest
from uuid import uuid4

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.base import SessionBase
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test.client import RequestFactory as drf


id = pytest.fixture(lambda: '2b88b740-3920-44e9-b086-c851f58e7ea7')


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
